"""
Tests for ISAF storage backends.
"""

import os
import pytest

from isaf.storage.base import StorageBackend
from isaf.storage.sqlite_backend import SQLiteBackend


class TestStorageBackend:
    """Tests for the abstract StorageBackend class."""

    def test_abstract_class(self):
        """Test that StorageBackend is abstract."""
        with pytest.raises(TypeError):
            StorageBackend()


class TestSQLiteBackend:
    """Tests for the SQLite storage backend."""

    def test_initialization(self, temp_db):
        """Test SQLite backend initialization creates database."""
        backend = SQLiteBackend(temp_db)

        assert os.path.exists(temp_db)
        assert backend.db_path == temp_db

    def test_store_and_retrieve(self, temp_db):
        """Test storing and retrieving layer data."""
        backend = SQLiteBackend(temp_db)

        layer_data = {
            'layer': 6,
            'session_id': 'test-session-123',
            'logged_at': '2024-01-15T10:00:00',
            'data': {
                'layer': 6,
                'layer_name': 'Framework Configuration',
                'frameworks': []
            }
        }

        backend.store(6, layer_data)
        result = backend.retrieve('test-session-123')

        assert result['session_id'] == 'test-session-123'
        assert '6' in result['layers']

    def test_store_multiple_layers(self, temp_db):
        """Test storing multiple layers for same session."""
        backend = SQLiteBackend(temp_db)
        session_id = 'multi-layer-session'

        for layer_num in [6, 7, 8]:
            backend.store(layer_num, {
                'layer': layer_num,
                'session_id': session_id,
                'logged_at': f'2024-01-15T10:0{layer_num}:00',
                'data': {'layer': layer_num}
            })

        result = backend.retrieve(session_id)

        assert len(result['layers']) == 3
        assert '6' in result['layers']
        assert '7' in result['layers']
        assert '8' in result['layers']

    def test_retrieve_nonexistent_session(self, temp_db):
        """Test retrieving non-existent session returns empty dict."""
        backend = SQLiteBackend(temp_db)

        result = backend.retrieve('nonexistent-session')

        assert result == {}

    def test_list_sessions(self, temp_db):
        """Test listing sessions."""
        backend = SQLiteBackend(temp_db)

        # Create multiple sessions
        for i in range(5):
            backend.store(6, {
                'layer': 6,
                'session_id': f'session-{i}',
                'logged_at': f'2024-01-{15+i:02d}T10:00:00',
                'data': {}
            })

        sessions = backend.list_sessions(limit=3)

        assert len(sessions) == 3
        # Should be ordered by created_at DESC
        for s in sessions:
            assert 'session_id' in s
            assert 'created_at' in s

    def test_list_sessions_empty_db(self, temp_db):
        """Test listing sessions on empty database."""
        backend = SQLiteBackend(temp_db)

        sessions = backend.list_sessions()

        assert sessions == []

    def test_get_latest_session(self, temp_db):
        """Test getting the latest session."""
        backend = SQLiteBackend(temp_db)

        # Create sessions
        backend.store(6, {
            'layer': 6,
            'session_id': 'old-session',
            'logged_at': '2024-01-01T10:00:00',
            'data': {'value': 'old'}
        })

        backend.store(6, {
            'layer': 6,
            'session_id': 'new-session',
            'logged_at': '2024-01-15T10:00:00',
            'data': {'value': 'new'}
        })

        result = backend.get_latest_session()

        assert result is not None
        assert result['session_id'] == 'new-session'

    def test_get_latest_session_empty_db(self, temp_db):
        """Test getting latest session from empty database."""
        backend = SQLiteBackend(temp_db)

        result = backend.get_latest_session()

        assert result is None

    def test_concurrent_sessions(self, temp_db):
        """Test handling multiple concurrent sessions."""
        backend = SQLiteBackend(temp_db)

        # Store layers for different sessions interleaved
        backend.store(6, {'layer': 6, 'session_id': 'session-a', 'logged_at': '2024-01-15T10:00:00', 'data': {}})
        backend.store(6, {'layer': 6, 'session_id': 'session-b', 'logged_at': '2024-01-15T10:00:01', 'data': {}})
        backend.store(7, {'layer': 7, 'session_id': 'session-a', 'logged_at': '2024-01-15T10:00:02', 'data': {}})
        backend.store(7, {'layer': 7, 'session_id': 'session-b', 'logged_at': '2024-01-15T10:00:03', 'data': {}})

        result_a = backend.retrieve('session-a')
        result_b = backend.retrieve('session-b')

        assert len(result_a['layers']) == 2
        assert len(result_b['layers']) == 2

    def test_schema_creation_idempotent(self, temp_db):
        """Test that schema creation is idempotent."""
        backend1 = SQLiteBackend(temp_db)
        backend1.store(6, {'layer': 6, 'session_id': 'test', 'logged_at': '2024-01-15', 'data': {}})

        # Creating another backend instance shouldn't fail
        backend2 = SQLiteBackend(temp_db)
        result = backend2.retrieve('test')

        assert result['session_id'] == 'test'
