"""
ISAF Hash Chain Generator

Provides cryptographic verification for lineage data integrity.
"""

import hashlib
import json
from typing import Any, Dict, List


class HashChainGenerator:
    """
    Generates and verifies cryptographic hash chains for lineage data.
    
    Uses SHA-256 hashing with canonical JSON serialization to ensure
    deterministic and verifiable hash chains.
    """
    
    def _canonical_json(self, data: Any) -> str:
        """Convert data to canonical JSON string."""
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash of a string."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def compute_layer_hash(
        self, 
        layer_data: Dict[str, Any], 
        previous_hash: str = ''
    ) -> str:
        """
        Compute hash for a layer, chained to previous hash.
        
        Args:
            layer_data: The layer data to hash
            previous_hash: Hash of the previous layer (empty for first layer)
        
        Returns:
            SHA-256 hash string
        """
        combined = previous_hash + self._canonical_json(layer_data)
        return self._compute_hash(combined)
    
    def generate_chain(self, lineage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete hash chain for lineage data.
        
        Args:
            lineage_data: Complete lineage dictionary with layers
        
        Returns:
            Hash chain dictionary with layer hashes and root hash
        """
        layers = lineage_data.get('layers', {})
        
        chain: Dict[str, Any] = {
            'algorithm': 'SHA-256',
            'layer_hashes': {},
            'root_hash': ''
        }
        
        previous_hash = ''
        sorted_layers = sorted(layers.keys(), key=lambda x: int(x))
        
        for layer_key in sorted_layers:
            layer_data = layers[layer_key]
            layer_hash = self.compute_layer_hash(layer_data, previous_hash)
            chain['layer_hashes'][layer_key] = layer_hash
            previous_hash = layer_hash
        
        metadata_hash = self._compute_hash(
            previous_hash + 
            self._canonical_json(lineage_data.get('session_id', '')) +
            self._canonical_json(lineage_data.get('created_at', ''))
        )
        
        chain['root_hash'] = metadata_hash
        
        return chain
    
    def verify_chain(
        self, 
        lineage_data: Dict[str, Any], 
        claimed_chain: Dict[str, Any]
    ) -> bool:
        """
        Verify the integrity of a lineage hash chain.
        
        Args:
            lineage_data: The lineage data to verify
            claimed_chain: The hash chain to verify against
        
        Returns:
            True if verification passes, False otherwise
        """
        computed_chain = self.generate_chain(lineage_data)
        
        if computed_chain['root_hash'] != claimed_chain.get('root_hash'):
            return False
        
        for layer_key, claimed_hash in claimed_chain.get('layer_hashes', {}).items():
            if computed_chain['layer_hashes'].get(layer_key) != claimed_hash:
                return False
        
        return True
