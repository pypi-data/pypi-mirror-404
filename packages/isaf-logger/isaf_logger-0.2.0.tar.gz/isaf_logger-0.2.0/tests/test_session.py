"""
Tests for ISAF session management.
"""

import os
import json
import pytest
import tempfile

import isaf
from isaf.core.session import ISAFSession, init, get_session, get_lineage, export, verify_lineage


class TestISAFSession:
    """Tests for the ISAFSession class."""

    def test_session_creation(self, temp_db):
        """Test creating a new session."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID format
        assert session.backend_type == 'sqlite'
        assert session.db_path == temp_db

    def test_session_memory_backend(self):
        """Test session with memory backend."""
        session = ISAFSession(backend='memory', auto_log_framework=False)

        assert session._backend is None
        assert session.backend_type == 'memory'

    def test_session_invalid_backend(self):
        """Test that invalid backend raises error."""
        with pytest.raises(ValueError, match="Unknown backend"):
            ISAFSession(backend='invalid_backend', auto_log_framework=False)

    def test_log_layer(self, temp_db):
        """Test logging layer data."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        layer_data = {
            'layer': 8,
            'layer_name': 'Test Objective',
            'objective': {'name': 'test_loss'}
        }

        session.log_layer(8, layer_data)

        assert 8 in session._layers
        assert session._layers[8]['data'] == layer_data

    def test_log_invalid_layer(self, temp_db):
        """Test that invalid layer number raises error."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        with pytest.raises(ValueError, match="Invalid layer number"):
            session.log_layer(5, {})

        with pytest.raises(ValueError, match="Invalid layer number"):
            session.log_layer(10, {})

    def test_log_layer9(self, temp_db):
        """Test logging Layer 9 (Deployment/Inference) data."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        layer_data = {
            'layer': 9,
            'layer_name': 'Deployment/Inference',
            'inference_config': {'mode': 'single'},
            'decision_boundary': {'thresholds': {'default': 0.5}}
        }

        session.log_layer(9, layer_data)

        assert 9 in session._layers
        assert session._layers[9]['data'] == layer_data

    def test_get_lineage(self, temp_db):
        """Test retrieving lineage data."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        session.log_layer(6, {'layer_name': 'Framework'})
        session.log_layer(7, {'layer_name': 'Data'})

        lineage = session.get_lineage()

        assert lineage['session_id'] == session.session_id
        assert '6' in lineage['layers']
        assert '7' in lineage['layers']
        assert lineage['metadata']['backend'] == 'sqlite'

    def test_export_creates_file(self, temp_db, temp_json):
        """Test that export creates a valid JSON file."""
        session = ISAFSession(backend='sqlite', db_path=temp_db, auto_log_framework=False)
        session.log_layer(6, {'layer_name': 'Framework'})

        output_path = session.export(temp_json)

        assert os.path.exists(output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert data['isaf_version'] == '1.0'
        assert data['session_id'] == session.session_id
        assert 'instruction_stack' in data


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_init_creates_global_session(self, temp_db, clean_isaf_session):
        """Test that init creates a global session."""
        session = init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        assert session is not None
        assert get_session() is session

    def test_get_lineage_without_init(self, clean_isaf_session):
        """Test that get_lineage raises error without init."""
        with pytest.raises(RuntimeError, match="ISAF not initialized"):
            get_lineage()

    def test_export_without_init(self, clean_isaf_session):
        """Test that export raises error without init."""
        with pytest.raises(RuntimeError, match="ISAF not initialized"):
            export('test.json')

    def test_full_workflow(self, temp_db, temp_json, clean_isaf_session):
        """Test complete init -> log -> export -> verify workflow."""
        # Initialize
        session = init(backend='sqlite', db_path=temp_db, auto_log_framework=False)

        # Log layers
        session.log_layer(6, {
            'layer': 6,
            'layer_name': 'Framework Configuration',
            'frameworks': []
        })
        session.log_layer(7, {
            'layer': 7,
            'layer_name': 'Training Data',
            'datasets': []
        })
        session.log_layer(8, {
            'layer': 8,
            'layer_name': 'Objective Function',
            'objective': {'name': 'mse'}
        })

        # Get lineage
        lineage = get_lineage()
        assert len(lineage['layers']) == 3

        # Export
        output_path = export(temp_json, include_hash_chain=True)
        assert os.path.exists(output_path)

        # Verify
        result = verify_lineage(output_path)
        assert result is True


class TestVerifyLineage:
    """Tests for lineage verification."""

    def test_verify_valid_lineage(self, sample_exported_document, temp_json):
        """Test verifying a valid exported document."""
        with open(temp_json, 'w') as f:
            json.dump(sample_exported_document, f)

        result = verify_lineage(temp_json)
        assert result is True

    def test_verify_tampered_lineage(self, sample_exported_document, temp_json):
        """Test that tampered document fails verification."""
        # Tamper with the document
        sample_exported_document['instruction_stack'][0]['data']['layer_name'] = 'TAMPERED'

        with open(temp_json, 'w') as f:
            json.dump(sample_exported_document, f)

        result = verify_lineage(temp_json)
        assert result is False

    def test_verify_missing_hash_chain(self, sample_exported_document, temp_json):
        """Test that document without hash chain fails."""
        del sample_exported_document['hash_chain']

        with open(temp_json, 'w') as f:
            json.dump(sample_exported_document, f)

        result = verify_lineage(temp_json)
        assert result is False
