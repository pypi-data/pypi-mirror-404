"""
ISAF Session Management

Provides the core session handling for ISAF logging, including
initialization, layer logging, lineage retrieval, and export.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from isaf.config import load_config

# Configure ISAF logger
logger = logging.getLogger('isaf')

_global_session: Optional['ISAFSession'] = None


class ISAFSession:
    """
    Main session class for ISAF logging.
    
    Manages the logging session, stores layer data, and coordinates
    with storage backends and exporters.
    """
    
    def __init__(
        self,
        backend: str = 'sqlite',
        db_path: Optional[str] = None,
        auto_log_framework: bool = True,
        **config: Any
    ):
        self.session_id = str(uuid.uuid4())
        self.backend_type = backend
        self.db_path = db_path or 'isaf_lineage.db'
        self.auto_log_framework = auto_log_framework
        self.config = config
        self.created_at = datetime.utcnow()
        
        self._layers: Dict[int, Dict[str, Any]] = {}
        self._backend = None
        
        self._init_backend()
        
        if auto_log_framework:
            self._log_framework_automatically()
    
    def _init_backend(self) -> None:
        """Initialize the storage backend."""
        if self.backend_type == 'sqlite':
            from isaf.storage.sqlite_backend import SQLiteBackend
            self._backend = SQLiteBackend(self.db_path)
        elif self.backend_type == 'mlflow':
            from isaf.storage.mlflow_backend import MLflowBackend
            tracking_uri = self.config.get('tracking_uri')
            self._backend = MLflowBackend(tracking_uri)
        elif self.backend_type == 'memory':
            self._backend = None
        else:
            raise ValueError(f"Unknown backend: {self.backend_type}")
    
    def _log_framework_automatically(self) -> None:
        """Automatically log Layer 6 framework information."""
        try:
            from isaf.core.extractors import Layer6Extractor

            extractor = Layer6Extractor()
            context = {
                'function_name': '__auto_detect__',
                'module': '__main__',
                'timestamp': datetime.utcnow().isoformat()
            }
            layer_data = extractor.extract(context)
            self.log_layer(6, layer_data)
        except Exception as e:
            logger.warning(f"Failed to auto-log framework (Layer 6): {e}")
    
    def log_layer(self, layer_num: int, data: Dict[str, Any]) -> None:
        """
        Log data for a specific layer.
        
        Args:
            layer_num: Layer number (6, 7, or 8)
            data: Layer data dictionary
        """
        if layer_num not in [6, 7, 8, 9]:
            raise ValueError(f"Invalid layer number: {layer_num}. Must be 6, 7, 8, or 9.")
        
        layer_data = {
            'layer': layer_num,
            'session_id': self.session_id,
            'logged_at': datetime.utcnow().isoformat(),
            'data': data
        }
        
        self._layers[layer_num] = layer_data
        
        if self._backend is not None:
            try:
                self._backend.store(layer_num, layer_data)
            except Exception as e:
                logger.error(f"Failed to store Layer {layer_num} data: {e}")
    
    def get_lineage(self) -> Dict[str, Any]:
        """
        Get the complete lineage for this session.
        
        Returns:
            Dictionary containing all logged layers and metadata
        """
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'layers': {
                str(k): v for k, v in sorted(self._layers.items())
            },
            'metadata': {
                'backend': self.backend_type,
                'isaf_version': '0.1.0'
            }
        }
    
    def export(
        self,
        output_path: str,
        include_hash_chain: bool = True,
        compliance_mappings: Optional[list] = None
    ) -> str:
        """
        Export lineage to a JSON file.
        
        Args:
            output_path: Path for the output file
            include_hash_chain: Whether to include cryptographic hash chain
            compliance_mappings: List of compliance frameworks to map to
        
        Returns:
            Path to the exported file
        """
        from isaf.export.exporter import ISAFExporter
        
        lineage = self.get_lineage()
        exporter = ISAFExporter()
        
        return exporter.export(
            lineage,
            output_path,
            include_hash_chain=include_hash_chain,
            compliance_mappings=compliance_mappings
        )


def init(
    backend: Optional[str] = None,
    db_path: Optional[str] = None,
    auto_log_framework: Optional[bool] = None,
    config_path: Optional[str] = None,
    **config: Any
) -> ISAFSession:
    """
    Initialize ISAF logging session.

    Configuration is loaded in this priority (highest to lowest):
    1. Function arguments passed directly
    2. Environment variables (ISAF_BACKEND, ISAF_DB_PATH, etc.)
    3. Config file (.isafrc or specified config_path)
    4. Default values

    Args:
        backend: Storage backend ('sqlite', 'mlflow', or 'memory')
        db_path: Path to database file (for sqlite backend)
        auto_log_framework: Automatically log Layer 6 on init
        config_path: Path to configuration file (default: .isafrc)
        **config: Additional configuration options

    Returns:
        The initialized ISAFSession

    Example:
        isaf.init(backend='sqlite', db_path='my_lineage.db')
    """
    global _global_session

    # Load configuration from file and environment
    loaded_config = load_config(config_path)

    # Configure logging level
    log_level = loaded_config.get('log_level', 'WARNING')
    logging.getLogger('isaf').setLevel(getattr(logging, log_level.upper(), logging.WARNING))

    # Apply configuration with explicit arguments taking priority
    final_backend = backend if backend is not None else loaded_config.get('backend', 'sqlite')
    final_db_path = db_path if db_path is not None else loaded_config.get('db_path', 'isaf_lineage.db')
    final_auto_log = auto_log_framework if auto_log_framework is not None else loaded_config.get('auto_log_framework', True)

    logger.debug(f"Initializing ISAF session with backend={final_backend}, db_path={final_db_path}")

    _global_session = ISAFSession(
        backend=final_backend,
        db_path=final_db_path,
        auto_log_framework=final_auto_log,
        **config
    )
    return _global_session


def get_session() -> Optional[ISAFSession]:
    """
    Get the current global session.
    
    Returns:
        The current ISAFSession or None if not initialized
    """
    return _global_session


def get_lineage(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get lineage data.
    
    Args:
        session_id: Optional session ID to retrieve (uses current if None)
    
    Returns:
        Lineage dictionary
    """
    if _global_session is None:
        raise RuntimeError("ISAF not initialized. Call isaf.init() first.")
    
    if session_id is not None and _global_session._backend is not None:
        return _global_session._backend.retrieve(session_id)
    
    return _global_session.get_lineage()


def export(
    output_path: str,
    include_hash_chain: bool = True,
    compliance_mappings: Optional[list] = None
) -> str:
    """
    Export current session lineage to file.
    
    Args:
        output_path: Path for the output file
        include_hash_chain: Include cryptographic verification
        compliance_mappings: Compliance frameworks to map
    
    Returns:
        Path to exported file
    """
    if _global_session is None:
        raise RuntimeError("ISAF not initialized. Call isaf.init() first.")
    
    return _global_session.export(
        output_path,
        include_hash_chain=include_hash_chain,
        compliance_mappings=compliance_mappings
    )


def verify_lineage(lineage_file: str) -> bool:
    """
    Verify the cryptographic integrity of a lineage file.

    Args:
        lineage_file: Path to the lineage JSON file

    Returns:
        True if verification passes, False otherwise
    """
    import json
    from isaf.verification.hash_chain import HashChainGenerator

    with open(lineage_file, 'r') as f:
        data = json.load(f)

    if 'hash_chain' not in data:
        return False

    # Reconstruct the original lineage_data format from the exported document
    # The hash chain was generated from this format, so we need to match it
    lineage_data = _reconstruct_lineage_data(data)

    generator = HashChainGenerator()
    return generator.verify_chain(lineage_data, data['hash_chain'])


def _reconstruct_lineage_data(exported_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconstruct the original lineage_data format from an exported ISAF document.

    The exporter transforms lineage_data into a different format for the exported
    document, but the hash chain is generated from the original format. This
    function reconstructs that format for verification.

    Args:
        exported_data: The exported ISAF document

    Returns:
        Reconstructed lineage_data in original format
    """
    layers = {}

    # Reconstruct layers from instruction_stack
    instruction_stack = exported_data.get('instruction_stack', [])
    for stack_entry in instruction_stack:
        layer_num = stack_entry.get('layer')
        if layer_num is not None:
            # Reconstruct the original layer format
            layers[str(layer_num)] = {
                'layer': layer_num,
                'session_id': exported_data.get('session_id'),
                'logged_at': stack_entry.get('logged_at'),
                'data': stack_entry.get('data', {})
            }

    return {
        'session_id': exported_data.get('session_id'),
        'created_at': exported_data.get('session_created_at'),
        'layers': layers,
        'metadata': exported_data.get('metadata', {})
    }
