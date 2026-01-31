"""
Tests for ISAF decorators.
"""

import pytest

import isaf
from isaf.decorators import (
    log_objective,
    log_data,
    log_framework,
    log_inference,
    log_all,
    _safe_get_source,
    _extract_arg_info,
    _is_data_like,
    _compute_data_hash
)


class TestHelperFunctions:
    """Tests for decorator helper functions."""

    def test_safe_get_source(self):
        """Test safe source extraction."""
        def sample_func():
            pass

        source = _safe_get_source(sample_func)
        assert source is not None
        assert 'def sample_func' in source

    def test_safe_get_source_builtin(self):
        """Test safe source extraction for builtin returns None."""
        source = _safe_get_source(len)
        assert source is None

    def test_extract_arg_info(self):
        """Test argument info extraction."""
        def func(a, b, c=10):
            pass

        info = _extract_arg_info(func, (1, 'test'), {'c': 20})

        assert 'a' in info
        assert info['a']['value'] == '1'
        assert 'b' in info
        assert info['b']['type'] == 'str'
        assert 'c' in info
        assert info['c']['value'] == '20'

    def test_extract_arg_info_with_shape(self):
        """Test argument info extraction for objects with shape."""
        class MockArray:
            shape = (100, 10)

        def func(data):
            pass

        info = _extract_arg_info(func, (MockArray(),), {})

        assert info['data']['shape'] == '(100, 10)'

    def test_is_data_like_true(self):
        """Test is_data_like returns True for data objects."""
        class MockDataFrame:
            pass

        class MockTensor:
            shape = (10, 10)

        assert _is_data_like(MockDataFrame()) is True
        assert _is_data_like(MockTensor()) is True
        assert _is_data_like([1, 2, 3]) is True

    def test_is_data_like_false(self):
        """Test is_data_like returns False for non-data objects."""
        assert _is_data_like(None) is False
        assert _is_data_like(42) is False
        # Note: strings have __len__ so they are considered "data-like"
        # This is intentional - string data could be text datasets

    def test_compute_data_hash(self):
        """Test data hash computation."""
        data = [1, 2, 3, 4, 5]

        hash1 = _compute_data_hash(data)
        hash2 = _compute_data_hash(data)
        hash3 = _compute_data_hash([5, 4, 3, 2, 1])

        assert hash1 is not None
        assert hash1 == hash2
        assert hash1 != hash3


class TestLogObjectiveDecorator:
    """Tests for the log_objective decorator."""

    def test_decorator_preserves_function(self, temp_db, clean_isaf_session):
        """Test that decorator preserves original function behavior."""
        isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_objective(name='test_loss')
        def train_model(epochs):
            return epochs * 2

        result = train_model(10)
        assert result == 20

    def test_decorator_logs_layer8(self, temp_db, clean_isaf_session):
        """Test that decorator logs Layer 8."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_objective(name='cross_entropy', constraints=['L2_reg'])
        def train():
            pass

        train()

        lineage = session.get_lineage()
        assert '8' in lineage['layers']
        assert lineage['layers']['8']['data']['objective']['name'] == 'cross_entropy'

    def test_decorator_without_session(self):
        """Test that decorator works gracefully without initialized session."""
        @log_objective(name='test')
        def train():
            return 42

        # Should not raise, just skip logging
        result = train()
        assert result == 42

    def test_decorator_with_justification(self, temp_db, clean_isaf_session):
        """Test decorator with justification parameter."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_objective(
            name='custom_loss',
            justification='Business requirement for weighted predictions'
        )
        def train():
            pass

        train()

        lineage = session.get_lineage()
        assert lineage['layers']['8']['data']['context']['justification'] == 'Business requirement for weighted predictions'


class TestLogDataDecorator:
    """Tests for the log_data decorator."""

    def test_decorator_preserves_return(self, temp_db, clean_isaf_session):
        """Test that decorator preserves return value."""
        isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_data(source='test')
        def load_data():
            return [1, 2, 3, 4, 5]

        result = load_data()
        assert result == [1, 2, 3, 4, 5]

    def test_decorator_logs_layer7(self, temp_db, clean_isaf_session):
        """Test that decorator logs Layer 7."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_data(source='internal', version='2024-01')
        def load_data():
            return [1, 2, 3]

        load_data()

        lineage = session.get_lineage()
        assert '7' in lineage['layers']
        layer7 = lineage['layers']['7']['data']
        assert layer7['context']['source'] == 'internal'
        assert layer7['context']['version'] == '2024-01'


class TestLogFrameworkDecorator:
    """Tests for the log_framework decorator."""

    def test_decorator_no_args(self, temp_db, clean_isaf_session):
        """Test decorator without arguments."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_framework
        def build_model():
            return 'model'

        result = build_model()
        assert result == 'model'

        lineage = session.get_lineage()
        assert '6' in lineage['layers']

    def test_decorator_with_parens(self, temp_db, clean_isaf_session):
        """Test decorator with empty parentheses."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_framework()
        def build_model():
            return 'model'

        result = build_model()
        assert result == 'model'


class TestLogAllDecorator:
    """Tests for the log_all decorator."""

    def test_decorator_logs_framework(self, temp_db, clean_isaf_session):
        """Test that log_all logs Layer 6."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_all
        def pipeline():
            return 'done'

        result = pipeline()
        assert result == 'done'

        lineage = session.get_lineage()
        assert '6' in lineage['layers']

    def test_decorator_logs_data_if_returned(self, temp_db, clean_isaf_session):
        """Test that log_all logs Layer 7 if function returns data-like object."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_all
        def load_data():
            return [1, 2, 3, 4, 5]  # list has __len__

        load_data()

        lineage = session.get_lineage()
        assert '6' in lineage['layers']
        assert '7' in lineage['layers']

    def test_decorator_no_data_layer_for_non_data(self, temp_db, clean_isaf_session):
        """Test that log_all doesn't log Layer 7 for non-data returns."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_all
        def simple_func():
            return 42  # int doesn't have __len__ or shape

        simple_func()

        lineage = session.get_lineage()
        assert '6' in lineage['layers']
        assert '7' not in lineage['layers']


class TestLogInferenceDecorator:
    """Tests for the log_inference decorator."""

    def test_decorator_preserves_return(self, temp_db, clean_isaf_session):
        """Test that decorator preserves return value."""
        isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_inference(threshold=0.5)
        def predict(data):
            return [0.8, 0.2]

        result = predict([1, 2, 3])
        assert result == [0.8, 0.2]

    def test_decorator_logs_layer9(self, temp_db, clean_isaf_session):
        """Test that decorator logs Layer 9."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_inference(threshold=0.5, model_version='1.0.0')
        def predict(data):
            return [0.7]

        predict([1, 2, 3])

        lineage = session.get_lineage()
        assert '9' in lineage['layers']
        layer9 = lineage['layers']['9']['data']
        assert layer9['layer_name'] == 'Deployment/Inference'
        assert layer9['model_info']['model_version'] == '1.0.0'

    def test_decorator_with_human_oversight(self, temp_db, clean_isaf_session):
        """Test decorator with human oversight enabled."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_inference(
            threshold=0.5,
            human_oversight=True,
            review_threshold=0.6
        )
        def predict(data):
            return [0.55]

        predict([1, 2, 3])

        lineage = session.get_lineage()
        layer9 = lineage['layers']['9']['data']
        assert layer9['human_oversight']['enabled'] is True
        assert layer9['human_oversight']['review_threshold'] == 0.6

    def test_decorator_with_multi_class_thresholds(self, temp_db, clean_isaf_session):
        """Test decorator with multi-class thresholds."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_inference(
            thresholds={'positive': 0.7, 'negative': 0.3},
            model_name='sentiment_classifier'
        )
        def classify(text):
            return {'positive': 0.8, 'negative': 0.2}

        classify("test text")

        lineage = session.get_lineage()
        layer9 = lineage['layers']['9']['data']
        assert layer9['decision_boundary']['thresholds']['positive'] == 0.7
        assert layer9['decision_boundary']['thresholds']['negative'] == 0.3
        assert layer9['model_info']['model_name'] == 'sentiment_classifier'

    def test_decorator_without_session(self):
        """Test that decorator works gracefully without initialized session."""
        @log_inference(threshold=0.5)
        def predict(data):
            return 42

        # Should not raise, just skip logging
        result = predict([1, 2, 3])
        assert result == 42

    def test_decorator_with_batch_mode(self, temp_db, clean_isaf_session):
        """Test decorator with batch inference mode."""
        session = isaf.init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        @log_inference(inference_mode='batch', threshold=0.5)
        def batch_predict(data):
            return [[0.8], [0.6], [0.9]]

        batch_predict([[1], [2], [3]])

        lineage = session.get_lineage()
        layer9 = lineage['layers']['9']['data']
        assert layer9['inference_config']['mode'] == 'batch'
