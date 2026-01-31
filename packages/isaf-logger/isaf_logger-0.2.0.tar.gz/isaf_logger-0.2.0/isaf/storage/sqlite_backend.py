"""
ISAF SQLite Storage Backend

Stores lineage data in a local SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from isaf.storage.base import StorageBackend


class SQLiteBackend(StorageBackend):
    """
    SQLite storage backend for ISAF.
    
    Stores layer data in a local SQLite database file.
    """
    
    def __init__(self, db_path: str = 'isaf_lineage.db'):
        self.db_path = db_path
        self._create_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_schema(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS layer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                layer INTEGER NOT NULL,
                data TEXT NOT NULL,
                logged_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_layer_logs_session 
            ON layer_logs(session_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def store(self, layer: int, data: Dict[str, Any]) -> None:
        """
        Store layer data in the database.
        
        Args:
            layer: Layer number (6, 7, or 8)
            data: Layer data dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        session_id = data.get('session_id')
        if session_id:
            cursor.execute(
                'SELECT id FROM sessions WHERE id = ?',
                (session_id,)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    'INSERT INTO sessions (id, created_at) VALUES (?, ?)',
                    (session_id, datetime.utcnow().isoformat())
                )
        
        cursor.execute(
            'INSERT INTO layer_logs (session_id, layer, data, logged_at) VALUES (?, ?, ?, ?)',
            (session_id, layer, json.dumps(data), datetime.utcnow().isoformat())
        )
        
        conn.commit()
        conn.close()
    
    def retrieve(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve lineage data for a session.
        
        Args:
            session_id: The session ID to retrieve
        
        Returns:
            Complete lineage dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM sessions WHERE id = ?',
            (session_id,)
        )
        session = cursor.fetchone()
        
        if session is None:
            conn.close()
            return {}
        
        cursor.execute(
            'SELECT layer, data FROM layer_logs WHERE session_id = ? ORDER BY layer',
            (session_id,)
        )
        logs = cursor.fetchall()
        
        conn.close()
        
        layers = {}
        for log in logs:
            layer_num = log['layer']
            layer_data = json.loads(log['data'])
            layers[str(layer_num)] = layer_data
        
        return {
            'session_id': session_id,
            'created_at': session['created_at'],
            'layers': layers,
            'metadata': json.loads(session['metadata']) if session['metadata'] else {}
        }
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
        
        Returns:
            List of session summaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, created_at FROM sessions ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        sessions = cursor.fetchall()
        
        conn.close()
        
        return [
            {'session_id': s['id'], 'created_at': s['created_at']}
            for s in sessions
        ]
    
    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent session's lineage.
        
        Returns:
            Lineage dictionary or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1'
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result is None:
            return None
        
        return self.retrieve(result['id'])
