"""
ISAF Storage Backend Base Class

Abstract base class for all storage backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class StorageBackend(ABC):
    """
    Abstract base class for ISAF storage backends.
    
    All storage backends must implement store() and retrieve() methods.
    """
    
    @abstractmethod
    def store(self, layer: int, data: Dict[str, Any]) -> None:
        """
        Store layer data.
        
        Args:
            layer: Layer number (6, 7, or 8)
            data: Layer data dictionary
        """
        pass
    
    @abstractmethod
    def retrieve(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve lineage data for a session.
        
        Args:
            session_id: The session ID to retrieve
        
        Returns:
            Complete lineage dictionary
        """
        pass
