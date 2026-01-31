"""
ISAF MLflow Storage Backend

Stores lineage data using MLflow Tracking for integration with MLOps pipelines.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from isaf.storage.base import StorageBackend


class MLflowBackend(StorageBackend):
    """
    MLflow storage backend for ISAF.

    Stores layer data as MLflow run artifacts and parameters,
    enabling integration with existing MLOps workflows.

    Requires mlflow to be installed: pip install mlflow
    """

    def __init__(self, tracking_uri: Optional[str] = None, experiment_name: str = 'isaf_lineage'):
        """
        Initialize MLflow backend.

        Args:
            tracking_uri: MLflow tracking server URI (uses default if None)
            experiment_name: Name of the MLflow experiment for ISAF logs
        """
        try:
            import mlflow
        except ImportError:
            raise ImportError(
                "MLflow is required for MLflowBackend. "
                "Install it with: pip install mlflow"
            )

        self.mlflow = mlflow
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self._current_run_id: Optional[str] = None
        self._session_run_map: Dict[str, str] = {}

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        mlflow.set_experiment(experiment_name)

    def _get_or_create_run(self, session_id: str) -> str:
        """Get existing run ID or create a new run for the session."""
        if session_id in self._session_run_map:
            return self._session_run_map[session_id]

        run = self.mlflow.start_run(run_name=f"isaf_session_{session_id[:8]}")
        run_id = run.info.run_id
        self._session_run_map[session_id] = run_id

        self.mlflow.log_param("isaf_session_id", session_id)
        self.mlflow.log_param("isaf_created_at", datetime.utcnow().isoformat())

        return run_id

    def store(self, layer: int, data: Dict[str, Any]) -> None:
        """
        Store layer data in MLflow.

        Args:
            layer: Layer number (6, 7, or 8)
            data: Layer data dictionary
        """
        session_id = data.get('session_id')
        if not session_id:
            raise ValueError("session_id is required in layer data")

        run_id = self._get_or_create_run(session_id)

        with self.mlflow.start_run(run_id=run_id):
            layer_key = f"layer_{layer}"

            self.mlflow.log_param(f"{layer_key}_logged_at", data.get('logged_at', ''))

            layer_data = data.get('data', {})

            for key, value in self._flatten_dict(layer_data, prefix=layer_key):
                if isinstance(value, (int, float)):
                    try:
                        self.mlflow.log_metric(key, value)
                    except Exception:
                        self.mlflow.log_param(key, str(value)[:250])
                elif isinstance(value, str) and len(value) <= 250:
                    try:
                        self.mlflow.log_param(key, value)
                    except Exception:
                        pass

            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                prefix=f'{layer_key}_'
            ) as f:
                json.dump(data, f, indent=2, default=str)
                temp_path = f.name

            try:
                self.mlflow.log_artifact(temp_path, artifact_path="isaf_layers")
            finally:
                os.unlink(temp_path)

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        prefix: str = '',
        sep: str = '_'
    ) -> List[tuple]:
        """Flatten a nested dictionary for MLflow logging."""
        items = []
        for key, value in d.items():
            new_key = f"{prefix}{sep}{key}" if prefix else key
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep))
            else:
                items.append((new_key, value))
        return items

    def retrieve(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve lineage data for a session from MLflow.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Complete lineage dictionary
        """
        from mlflow.tracking import MlflowClient

        client = MlflowClient(self.tracking_uri)

        experiment = client.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            return {}

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"params.isaf_session_id = '{session_id}'",
            max_results=1
        )

        if not runs:
            return {}

        run = runs[0]
        run_id = run.info.run_id

        layers = {}

        artifacts_path = client.download_artifacts(run_id, "isaf_layers")

        import os
        if os.path.exists(artifacts_path):
            for filename in os.listdir(artifacts_path):
                if filename.endswith('.json') and filename.startswith('layer_'):
                    layer_num = filename.split('_')[1].split('.')[0]
                    filepath = os.path.join(artifacts_path, filename)
                    with open(filepath, 'r') as f:
                        layer_data = json.load(f)
                        layers[layer_num] = layer_data

        created_at = run.data.params.get('isaf_created_at', '')

        return {
            'session_id': session_id,
            'created_at': created_at,
            'layers': layers,
            'metadata': {
                'mlflow_run_id': run_id,
                'mlflow_experiment': self.experiment_name
            }
        }

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent ISAF sessions from MLflow.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        from mlflow.tracking import MlflowClient

        client = MlflowClient(self.tracking_uri)

        experiment = client.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            return []

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=limit
        )

        sessions = []
        for run in runs:
            session_id = run.data.params.get('isaf_session_id')
            created_at = run.data.params.get('isaf_created_at')
            if session_id:
                sessions.append({
                    'session_id': session_id,
                    'created_at': created_at,
                    'mlflow_run_id': run.info.run_id
                })

        return sessions

    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent session's lineage from MLflow.

        Returns:
            Lineage dictionary or None
        """
        sessions = self.list_sessions(limit=1)
        if not sessions:
            return None

        return self.retrieve(sessions[0]['session_id'])

    def end_run(self) -> None:
        """End the current MLflow run if one is active."""
        try:
            self.mlflow.end_run()
        except Exception:
            pass
