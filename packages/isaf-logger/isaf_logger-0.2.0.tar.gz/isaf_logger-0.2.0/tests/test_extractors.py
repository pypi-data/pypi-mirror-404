"""
Tests for ISAF layer extractors.
"""

import pytest
from datetime import datetime

from isaf.core.extractors import Layer6Extractor, Layer7Extractor, Layer8Extractor, Layer9Extractor


class TestLayer6Extractor:
    """Tests for Framework layer extraction."""

    def test_extract_basic(self):
        """Test basic extraction returns expected structure."""
        extractor = Layer6Extractor()
        context = {
            'function_name': 'build_model',
            'module': 'test_module',
            'timestamp': datetime.utcnow().isoformat()
        }

        result = extractor.extract(context)

        assert result['layer'] == 6
        assert result['layer_name'] == 'Framework Configuration'
        assert 'extracted_at' in result
        assert 'frameworks' in result
        assert 'defaults' in result
        assert 'precision' in result
        assert 'dependencies' in result
        assert 'system' in result
        assert result['context']['function'] == 'build_model'
        assert result['context']['module'] == 'test_module'

    def test_extract_system_info(self):
        """Test system info extraction."""
        extractor = Layer6Extractor()
        system_info = extractor._get_system_info()

        assert 'python_version' in system_info
        assert 'platform' in system_info
        assert 'processor' in system_info
        assert 'machine' in system_info

    def test_detect_frameworks_empty(self):
        """Test framework detection when none are loaded."""
        extractor = Layer6Extractor()
        frameworks = extractor._detect_frameworks()

        # Should return list (may be empty or contain frameworks already imported)
        assert isinstance(frameworks, list)

    def test_precision_detection(self):
        """Test precision detection."""
        extractor = Layer6Extractor()
        precision = extractor._detect_precision()

        assert 'default' in precision
        assert precision['default'] == 'float32'


class TestLayer7Extractor:
    """Tests for Training Data layer extraction."""

    def test_extract_basic(self):
        """Test basic extraction returns expected structure."""
        extractor = Layer7Extractor()
        context = {
            'function_name': 'load_data',
            'module': 'test_module',
            'source': 'internal',
            'version': '2024-01',
            'returned_data': None,
            'data_hash': 'abc123',
            'timestamp': datetime.utcnow().isoformat()
        }

        result = extractor.extract(context)

        assert result['layer'] == 7
        assert result['layer_name'] == 'Training Data'
        assert 'extracted_at' in result
        assert 'datasets' in result
        assert 'preprocessing' in result
        assert 'provenance' in result
        assert result['context']['source'] == 'internal'
        assert result['context']['version'] == '2024-01'

    def test_analyze_list_data(self):
        """Test analyzing list-like data."""
        extractor = Layer7Extractor()
        data = [1, 2, 3, 4, 5]
        context = {'data_hash': 'test123'}

        result = extractor._analyze_datasets(data, context)

        assert len(result) == 1
        assert result[0]['type'] == 'list'
        assert result[0]['length'] == 5

    def test_analyze_none_data(self):
        """Test analyzing None returns empty list."""
        extractor = Layer7Extractor()
        result = extractor._analyze_datasets(None, {})
        assert result == []

    def test_provenance_extraction(self):
        """Test provenance extraction."""
        extractor = Layer7Extractor()
        context = {
            'source': 'vendor_x',
            'version': 'v2.0',
            'data_hash': 'hash123',
            'timestamp': '2024-01-15T10:00:00'
        }

        result = extractor._extract_provenance(context)

        assert result['source'] == 'vendor_x'
        assert result['version'] == 'v2.0'
        assert result['data_hash'] == 'hash123'


class TestLayer8Extractor:
    """Tests for Objective Function layer extraction."""

    def test_extract_basic(self):
        """Test basic extraction returns expected structure."""
        extractor = Layer8Extractor()
        context = {
            'function_name': 'train',
            'module': 'test_module',
            'objective_name': 'cross_entropy',
            'constraints': ['L2_reg'],
            'justification': 'Standard classification loss',
            'source_code': 'def train(): pass',
            'arguments': {},
            'timestamp': datetime.utcnow().isoformat()
        }

        result = extractor.extract(context)

        assert result['layer'] == 8
        assert result['layer_name'] == 'Objective Function'
        assert 'extracted_at' in result
        assert 'objective' in result
        assert 'constraints' in result
        assert 'hyperparameters' in result
        assert result['context']['justification'] == 'Standard classification loss'

    def test_objective_mathematical_form_detection(self):
        """Test that mathematical forms are detected."""
        extractor = Layer8Extractor()

        context = {'objective_name': 'cross_entropy_loss'}
        result = extractor._extract_objective(context)
        assert result['mathematical_form'] is not None
        assert 'log' in result['mathematical_form']

        context = {'objective_name': 'mse_loss'}
        result = extractor._extract_objective(context)
        assert result['mathematical_form'] is not None
        assert 'MSE' in result['mathematical_form']

    def test_constraint_type_inference(self):
        """Test constraint type inference."""
        extractor = Layer8Extractor()

        assert extractor._infer_constraint_type('L1_regularization') == 'L1_regularization'
        assert extractor._infer_constraint_type('L2_weight_decay') == 'L2_regularization'
        assert extractor._infer_constraint_type('dropout_0.5') == 'dropout_regularization'
        assert extractor._infer_constraint_type('gradient_clipping') == 'gradient_constraint'
        assert extractor._infer_constraint_type('early_stopping') == 'early_stopping'
        assert extractor._infer_constraint_type('custom_constraint') == 'custom'

    def test_hyperparameter_extraction(self):
        """Test hyperparameter extraction from arguments."""
        extractor = Layer8Extractor()
        context = {
            'arguments': {
                'learning_rate': {'value': '0.001'},
                'batch_size': {'value': '32'},
                'epochs': {'value': '100'},
                'model': {'type': 'object'},  # Not a hyperparameter
                'data': {'type': 'tensor'}  # Not a hyperparameter
            }
        }

        result = extractor._extract_hyperparameters(context)

        assert 'learning_rate' in result
        assert 'batch_size' in result
        assert 'epochs' in result
        assert 'model' not in result
        assert 'data' not in result

    def test_extract_constraints(self):
        """Test constraint extraction."""
        extractor = Layer8Extractor()

        context = {'constraints': ['L2_reg', 'dropout']}
        result = extractor._extract_constraints(context)

        assert len(result) == 2
        assert result[0]['name'] == 'L2_reg'
        assert result[1]['name'] == 'dropout'


class TestLayer9Extractor:
    """Tests for Deployment/Inference layer extraction."""

    def test_extract_basic(self):
        """Test basic extraction returns expected structure."""
        extractor = Layer9Extractor()
        context = {
            'function_name': 'predict',
            'module': 'test_module',
            'threshold': 0.5,
            'model_version': '1.2.0',
            'human_oversight': True,
            'timestamp': datetime.utcnow().isoformat()
        }

        result = extractor.extract(context)

        assert result['layer'] == 9
        assert result['layer_name'] == 'Deployment/Inference'
        assert 'extracted_at' in result
        assert 'inference_config' in result
        assert 'decision_boundary' in result
        assert 'human_oversight' in result
        assert 'serving' in result
        assert 'model_info' in result
        assert result['context']['function'] == 'predict'

    def test_extract_decision_boundary(self):
        """Test decision boundary extraction."""
        extractor = Layer9Extractor()
        context = {
            'threshold': 0.7,
            'confidence_required': 0.9,
            'fallback_action': 'flag'
        }

        result = extractor._extract_decision_boundary(context)

        assert result['thresholds'] == {'default': 0.7}
        assert result['confidence_required'] == 0.9
        assert result['fallback_action'] == 'flag'

    def test_extract_multi_class_thresholds(self):
        """Test multi-class threshold extraction."""
        extractor = Layer9Extractor()
        context = {
            'thresholds': {'positive': 0.8, 'negative': 0.3, 'neutral': 0.5}
        }

        result = extractor._extract_decision_boundary(context)

        assert result['thresholds']['positive'] == 0.8
        assert result['thresholds']['negative'] == 0.3
        assert result['thresholds']['neutral'] == 0.5

    def test_extract_human_oversight(self):
        """Test human oversight extraction."""
        extractor = Layer9Extractor()
        context = {
            'human_oversight': True,
            'review_threshold': 0.6,
            'human_in_loop': True,
            'explanation_required': True
        }

        result = extractor._extract_human_oversight(context)

        assert result['enabled'] is True
        assert result['review_threshold'] == 0.6
        assert result['human_in_loop'] is True
        assert result['explanation_required'] is True
        assert result['audit_logging'] is True  # default

    def test_extract_inference_config(self):
        """Test inference config extraction."""
        extractor = Layer9Extractor()
        context = {
            'inference_mode': 'batch',
            'batch_size': 32,
            'timeout_ms': 1000
        }

        result = extractor._extract_inference_config(context)

        assert result['mode'] == 'batch'
        assert result['batch_size'] == 32
        assert result['timeout_ms'] == 1000

    def test_extract_model_info(self):
        """Test model info extraction."""
        extractor = Layer9Extractor()
        context = {
            'model_version': '2.0.0',
            'model_name': 'classifier_v2',
            'model_hash': 'abc123',
            'quantized': True
        }

        result = extractor._extract_model_info(context)

        assert result['model_version'] == '2.0.0'
        assert result['model_name'] == 'classifier_v2'
        assert result['model_hash'] == 'abc123'
        assert result['quantized'] is True

    def test_detect_environment_unknown(self):
        """Test environment detection returns unknown when no indicators."""
        extractor = Layer9Extractor()
        # Without setting environment variables, should return 'unknown'
        result = extractor._detect_environment()
        assert isinstance(result, str)

    def test_detect_serving_framework(self):
        """Test serving framework detection."""
        extractor = Layer9Extractor()
        result = extractor._detect_serving_framework()

        assert 'frameworks' in result
        assert 'detected_at' in result
        assert isinstance(result['frameworks'], list)
