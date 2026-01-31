"""
ISAF Configuration Management

Handles loading and merging configuration from files and environment variables.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    'backend': 'sqlite',
    'db_path': 'isaf_lineage.db',
    'auto_log_framework': True,
    'include_hash_chain': True,
    'log_level': 'WARNING'
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load ISAF configuration.
    
    Priority (highest to lowest):
    1. Environment variables (ISAF_BACKEND, ISAF_DB_PATH, etc.)
    2. Specified config file
    3. .isafrc in current directory
    4. Default values
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Merged configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path:
        config = _merge_config(config, _load_file(config_path))
    else:
        isafrc = Path('.isafrc')
        if isafrc.exists():
            config = _merge_config(config, _load_file(str(isafrc)))
    
    env_overrides = _load_env_vars()
    config = _merge_config(config, env_overrides)
    
    return config


def _load_file(path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_env_vars() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    env_config: Dict[str, Any] = {}
    
    env_mappings = {
        'ISAF_BACKEND': 'backend',
        'ISAF_DB_PATH': 'db_path',
        'ISAF_AUTO_LOG_FRAMEWORK': 'auto_log_framework',
        'ISAF_INCLUDE_HASH_CHAIN': 'include_hash_chain',
        'ISAF_LOG_LEVEL': 'log_level'
    }
    
    for env_var, config_key in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            if config_key in ['auto_log_framework', 'include_hash_chain']:
                env_config[config_key] = value.lower() in ('true', '1', 'yes')
            else:
                env_config[config_key] = value
    
    return env_config


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries."""
    result = base.copy()
    result.update(override)
    return result
