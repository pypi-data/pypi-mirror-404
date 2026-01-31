"""
Tests for ISAF CLI commands.
"""

import os
import json
import pytest
from click.testing import CliRunner

from isaf.cli import cli
from isaf.storage.sqlite_backend import SQLiteBackend
from isaf.export.exporter import ISAFExporter


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def populated_db(temp_db):
    """Create a database with sample data."""
    backend = SQLiteBackend(temp_db)

    backend.store(6, {
        'layer': 6,
        'session_id': 'cli-test-session',
        'logged_at': '2024-01-15T10:00:00',
        'data': {
            'layer': 6,
            'layer_name': 'Framework Configuration',
            'frameworks': [{'name': 'PyTorch', 'version': '2.0.0'}],
            'system': {'python_version': '3.10.0'}
        }
    })

    backend.store(7, {
        'layer': 7,
        'session_id': 'cli-test-session',
        'logged_at': '2024-01-15T10:00:01',
        'data': {
            'layer': 7,
            'layer_name': 'Training Data',
            'datasets': []
        }
    })

    return temp_db


@pytest.fixture
def sample_lineage_file(sample_exported_document, temp_json):
    """Create a sample lineage file."""
    with open(temp_json, 'w') as f:
        json.dump(sample_exported_document, f)
    return temp_json


class TestInspectCommand:
    """Tests for the inspect command."""

    def test_inspect_basic(self, cli_runner, sample_lineage_file):
        """Test basic inspect command."""
        result = cli_runner.invoke(cli, ['inspect', sample_lineage_file])

        assert result.exit_code == 0
        assert 'ISAF LINEAGE REPORT' in result.output
        assert 'Audit ID:' in result.output
        assert 'Session ID:' in result.output
        assert 'Layers Logged:' in result.output

    def test_inspect_shows_layers(self, cli_runner, sample_lineage_file):
        """Test that inspect shows layer information."""
        result = cli_runner.invoke(cli, ['inspect', sample_lineage_file])

        assert 'Layer 6:' in result.output
        assert 'Layer 7:' in result.output
        assert 'Layer 8:' in result.output
        assert 'Framework Configuration' in result.output

    def test_inspect_shows_hash_chain(self, cli_runner, sample_lineage_file):
        """Test that inspect shows hash chain info."""
        result = cli_runner.invoke(cli, ['inspect', sample_lineage_file])

        assert 'Hash Chain:' in result.output
        assert 'Present' in result.output
        assert 'SHA-256' in result.output

    def test_inspect_nonexistent_file(self, cli_runner):
        """Test inspect with nonexistent file."""
        result = cli_runner.invoke(cli, ['inspect', 'nonexistent.json'])

        assert result.exit_code != 0


class TestVerifyCommand:
    """Tests for the verify command."""

    def test_verify_valid_file(self, cli_runner, sample_lineage_file):
        """Test verifying a valid file."""
        result = cli_runner.invoke(cli, ['verify', sample_lineage_file])

        assert result.exit_code == 0
        assert 'VERIFICATION PASSED' in result.output

    def test_verify_tampered_file(self, cli_runner, sample_exported_document, temp_json):
        """Test verifying a tampered file."""
        # Tamper with the document
        sample_exported_document['instruction_stack'][0]['data']['layer_name'] = 'TAMPERED'

        with open(temp_json, 'w') as f:
            json.dump(sample_exported_document, f)

        result = cli_runner.invoke(cli, ['verify', temp_json])

        assert result.exit_code == 1
        assert 'VERIFICATION FAILED' in result.output

    def test_verify_no_hash_chain(self, cli_runner, sample_exported_document, temp_json):
        """Test verifying file without hash chain."""
        del sample_exported_document['hash_chain']

        with open(temp_json, 'w') as f:
            json.dump(sample_exported_document, f)

        result = cli_runner.invoke(cli, ['verify', temp_json])

        assert result.exit_code == 1


class TestExportFromDbCommand:
    """Tests for the export-from-db command."""

    def test_export_latest_session(self, cli_runner, populated_db, temp_json):
        """Test exporting latest session from database."""
        result = cli_runner.invoke(cli, [
            'export-from-db', populated_db,
            '-o', temp_json
        ])

        assert result.exit_code == 0
        assert 'Exported to:' in result.output
        assert os.path.exists(temp_json)

        with open(temp_json) as f:
            data = json.load(f)

        assert data['session_id'] == 'cli-test-session'

    def test_export_with_compliance(self, cli_runner, populated_db, temp_json):
        """Test exporting with compliance mappings."""
        result = cli_runner.invoke(cli, [
            'export-from-db', populated_db,
            '-o', temp_json,
            '-c', 'eu_ai_act',
            '-c', 'nist_ai_rmf'
        ])

        assert result.exit_code == 0

        with open(temp_json) as f:
            data = json.load(f)

        assert 'compliance' in data
        assert 'eu_ai_act' in data['compliance']
        assert 'nist_ai_rmf' in data['compliance']

    def test_export_specific_session(self, cli_runner, populated_db, temp_json):
        """Test exporting specific session."""
        result = cli_runner.invoke(cli, [
            'export-from-db', populated_db,
            '-o', temp_json,
            '-s', 'cli-test-session'
        ])

        assert result.exit_code == 0

    def test_export_nonexistent_session(self, cli_runner, populated_db, temp_json):
        """Test exporting nonexistent session."""
        result = cli_runner.invoke(cli, [
            'export-from-db', populated_db,
            '-o', temp_json,
            '-s', 'nonexistent-session'
        ])

        assert result.exit_code == 1
        assert 'No lineage data found' in result.output

    def test_export_empty_database(self, cli_runner, temp_db, temp_json):
        """Test exporting from empty database."""
        # Initialize empty db
        SQLiteBackend(temp_db)

        result = cli_runner.invoke(cli, [
            'export-from-db', temp_db,
            '-o', temp_json
        ])

        assert result.exit_code == 1
        assert 'No lineage data found' in result.output


class TestListSessionsCommand:
    """Tests for the list-sessions command."""

    def test_list_sessions(self, cli_runner, populated_db):
        """Test listing sessions."""
        result = cli_runner.invoke(cli, ['list-sessions', populated_db])

        assert result.exit_code == 0
        assert 'Recent Sessions' in result.output
        assert 'cli-test' in result.output  # Truncated session ID

    def test_list_sessions_with_limit(self, cli_runner, temp_db):
        """Test listing sessions with limit."""
        backend = SQLiteBackend(temp_db)

        # Create multiple sessions
        for i in range(10):
            backend.store(6, {
                'layer': 6,
                'session_id': f'session-{i:02d}',
                'logged_at': f'2024-01-{15+i:02d}T10:00:00',
                'data': {}
            })

        result = cli_runner.invoke(cli, ['list-sessions', temp_db, '-n', '3'])

        assert result.exit_code == 0
        # Should only show 3 sessions
        assert result.output.count('session-') == 3

    def test_list_sessions_empty_db(self, cli_runner, temp_db):
        """Test listing sessions from empty database."""
        SQLiteBackend(temp_db)

        result = cli_runner.invoke(cli, ['list-sessions', temp_db])

        assert result.exit_code == 0
        assert 'No sessions found' in result.output


class TestVersionCommand:
    """Tests for the version option."""

    def test_version(self, cli_runner):
        """Test --version option."""
        result = cli_runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output
