"""
Tests for ISAF exporter.
"""

import os
import json
import pytest

from isaf.export.exporter import ISAFExporter


class TestISAFExporter:
    """Tests for the ISAFExporter class."""

    def test_export_basic(self, sample_lineage_data, temp_json):
        """Test basic export functionality."""
        exporter = ISAFExporter()

        output_path = exporter.export(
            sample_lineage_data,
            temp_json,
            include_hash_chain=False
        )

        assert os.path.exists(output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert data['isaf_version'] == '1.0'
        assert 'audit_id' in data
        assert data['session_id'] == sample_lineage_data['session_id']
        assert 'instruction_stack' in data
        assert len(data['instruction_stack']) == 3

    def test_export_with_hash_chain(self, sample_lineage_data, temp_json):
        """Test export with hash chain included."""
        exporter = ISAFExporter()

        exporter.export(sample_lineage_data, temp_json, include_hash_chain=True)

        with open(temp_json) as f:
            data = json.load(f)

        assert 'hash_chain' in data
        assert data['hash_chain']['algorithm'] == 'SHA-256'
        assert 'root_hash' in data['hash_chain']
        assert 'layer_hashes' in data['hash_chain']

    def test_export_compliance_mappings(self, sample_lineage_data, temp_json):
        """Test export with compliance framework mappings."""
        exporter = ISAFExporter()

        exporter.export(
            sample_lineage_data,
            temp_json,
            include_hash_chain=False,
            compliance_mappings=['eu_ai_act', 'nist_ai_rmf', 'iso_42001']
        )

        with open(temp_json) as f:
            data = json.load(f)

        assert 'compliance' in data
        assert 'eu_ai_act' in data['compliance']
        assert 'nist_ai_rmf' in data['compliance']
        assert 'iso_42001' in data['compliance']

        # Check EU AI Act mapping
        eu_mapping = data['compliance']['eu_ai_act']
        assert eu_mapping['framework_name'] == 'EU AI Act'
        assert 'covered_requirements' in eu_mapping
        assert 'missing_requirements' in eu_mapping
        assert 'coverage_percentage' in eu_mapping

    def test_export_unknown_compliance_framework(self, sample_lineage_data, temp_json):
        """Test that unknown compliance frameworks are ignored."""
        exporter = ISAFExporter()

        exporter.export(
            sample_lineage_data,
            temp_json,
            compliance_mappings=['unknown_framework', 'eu_ai_act']
        )

        with open(temp_json) as f:
            data = json.load(f)

        assert 'compliance' in data
        assert 'unknown_framework' not in data['compliance']
        assert 'eu_ai_act' in data['compliance']

    def test_build_stack_trace(self, sample_lineage_data):
        """Test instruction stack building."""
        exporter = ISAFExporter()

        stack = exporter._build_stack_trace(sample_lineage_data)

        assert len(stack) == 3

        # Check layer 6
        layer6 = stack[0]
        assert layer6['layer'] == 6
        assert layer6['layer_name'] == 'Framework Configuration'
        assert layer6['owner'] == 'ML Engineer / Platform Team'

        # Check layer 7
        layer7 = stack[1]
        assert layer7['layer'] == 7
        assert layer7['owner'] == 'Data Engineer / Data Science Team'

        # Check layer 8
        layer8 = stack[2]
        assert layer8['layer'] == 8
        assert layer8['owner'] == 'Data Scientist / ML Engineer'

    def test_extract_system_info(self, sample_lineage_data):
        """Test system info extraction from Layer 6."""
        exporter = ISAFExporter()

        system_info = exporter._extract_system_info(sample_lineage_data)

        assert system_info == {'python_version': '3.10.0'}

    def test_coverage_percentage_calculation(self, sample_lineage_data, temp_json):
        """Test that coverage percentage is calculated correctly."""
        exporter = ISAFExporter()

        # With all layers (6, 7, 8), coverage should be 100%
        exporter.export(
            sample_lineage_data,
            temp_json,
            compliance_mappings=['eu_ai_act']
        )

        with open(temp_json) as f:
            data = json.load(f)

        # Layers 6, 7, 8 present (not 9), so 75% coverage (6/8 requirements)
        assert data['compliance']['eu_ai_act']['coverage_percentage'] == 75.0

    def test_partial_coverage(self, temp_json):
        """Test coverage with partial layers."""
        exporter = ISAFExporter()

        # Only layer 6
        partial_lineage = {
            'session_id': 'partial-session',
            'created_at': '2024-01-15T10:00:00',
            'layers': {
                '6': {
                    'layer': 6,
                    'session_id': 'partial-session',
                    'logged_at': '2024-01-15T10:00:01',
                    'data': {'layer': 6, 'layer_name': 'Framework'}
                }
            }
        }

        exporter.export(
            partial_lineage,
            temp_json,
            compliance_mappings=['eu_ai_act']
        )

        with open(temp_json) as f:
            data = json.load(f)

        # Only 1 of 4 layers, so 25% coverage (2/8 requirements)
        coverage = data['compliance']['eu_ai_act']['coverage_percentage']
        assert coverage == 25.0

    def test_export_creates_parent_directories(self, sample_lineage_data, temp_json):
        """Test that export creates parent directories if needed."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            nested_path = os.path.join(temp_dir, 'nested', 'dir', 'output.json')

            exporter = ISAFExporter()
            output_path = exporter.export(sample_lineage_data, nested_path)

            assert os.path.exists(output_path)
        finally:
            shutil.rmtree(temp_dir)

    def test_layer_owner_mapping(self):
        """Test layer owner mapping."""
        exporter = ISAFExporter()

        assert exporter._get_layer_owner(6) == 'ML Engineer / Platform Team'
        assert exporter._get_layer_owner(7) == 'Data Engineer / Data Science Team'
        assert exporter._get_layer_owner(8) == 'Data Scientist / ML Engineer'
        assert exporter._get_layer_owner(99) == 'Unknown'
