"""
Tests for ISAF hash chain generation and verification.
"""

import pytest
import copy

from isaf.verification.hash_chain import HashChainGenerator


class TestHashChainGenerator:
    """Tests for the HashChainGenerator class."""

    def test_compute_hash(self):
        """Test basic hash computation."""
        generator = HashChainGenerator()

        hash1 = generator._compute_hash("test data")
        hash2 = generator._compute_hash("test data")
        hash3 = generator._compute_hash("different data")

        # Same input should produce same hash
        assert hash1 == hash2
        # Different input should produce different hash
        assert hash1 != hash3
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64

    def test_canonical_json(self):
        """Test canonical JSON serialization."""
        generator = HashChainGenerator()

        # Order shouldn't matter
        json1 = generator._canonical_json({'b': 2, 'a': 1})
        json2 = generator._canonical_json({'a': 1, 'b': 2})

        assert json1 == json2
        assert json1 == '{"a":1,"b":2}'

    def test_compute_layer_hash_chaining(self):
        """Test that layer hashes are properly chained."""
        generator = HashChainGenerator()

        layer1 = {'layer': 6, 'data': 'test1'}
        layer2 = {'layer': 7, 'data': 'test2'}

        # Hash without previous
        hash1 = generator.compute_layer_hash(layer1, '')

        # Hash with previous should be different
        hash2 = generator.compute_layer_hash(layer2, hash1)
        hash2_no_chain = generator.compute_layer_hash(layer2, '')

        assert hash2 != hash2_no_chain

    def test_generate_chain(self, sample_lineage_data):
        """Test complete chain generation."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)

        assert chain['algorithm'] == 'SHA-256'
        assert 'layer_hashes' in chain
        assert 'root_hash' in chain
        assert len(chain['root_hash']) == 64

        # Should have hashes for each layer
        assert '6' in chain['layer_hashes']
        assert '7' in chain['layer_hashes']
        assert '8' in chain['layer_hashes']

    def test_generate_chain_empty_layers(self):
        """Test chain generation with no layers."""
        generator = HashChainGenerator()
        lineage = {
            'session_id': 'test',
            'created_at': '2024-01-01',
            'layers': {}
        }

        chain = generator.generate_chain(lineage)

        assert chain['algorithm'] == 'SHA-256'
        assert chain['layer_hashes'] == {}
        assert len(chain['root_hash']) == 64

    def test_verify_chain_valid(self, sample_lineage_data):
        """Test that valid chain passes verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)
        result = generator.verify_chain(sample_lineage_data, chain)

        assert result is True

    def test_verify_chain_tampered_layer(self, sample_lineage_data):
        """Test that tampered layer fails verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)

        # Tamper with layer data
        tampered = copy.deepcopy(sample_lineage_data)
        tampered['layers']['6']['data']['layer_name'] = 'TAMPERED'

        result = generator.verify_chain(tampered, chain)

        assert result is False

    def test_verify_chain_tampered_session_id(self, sample_lineage_data):
        """Test that tampered session_id fails verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)

        # Tamper with session_id
        tampered = copy.deepcopy(sample_lineage_data)
        tampered['session_id'] = 'tampered-session-id'

        result = generator.verify_chain(tampered, chain)

        assert result is False

    def test_verify_chain_tampered_timestamp(self, sample_lineage_data):
        """Test that tampered timestamp fails verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)

        # Tamper with created_at
        tampered = copy.deepcopy(sample_lineage_data)
        tampered['created_at'] = '2024-12-31T23:59:59'

        result = generator.verify_chain(tampered, chain)

        assert result is False

    def test_verify_chain_wrong_root_hash(self, sample_lineage_data):
        """Test that wrong root hash fails verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)
        chain['root_hash'] = 'a' * 64  # Wrong hash

        result = generator.verify_chain(sample_lineage_data, chain)

        assert result is False

    def test_verify_chain_wrong_layer_hash(self, sample_lineage_data):
        """Test that wrong layer hash fails verification."""
        generator = HashChainGenerator()

        chain = generator.generate_chain(sample_lineage_data)
        chain['layer_hashes']['7'] = 'b' * 64  # Wrong hash

        result = generator.verify_chain(sample_lineage_data, chain)

        assert result is False

    def test_chain_deterministic(self, sample_lineage_data):
        """Test that chain generation is deterministic."""
        generator = HashChainGenerator()

        chain1 = generator.generate_chain(sample_lineage_data)
        chain2 = generator.generate_chain(sample_lineage_data)

        assert chain1['root_hash'] == chain2['root_hash']
        assert chain1['layer_hashes'] == chain2['layer_hashes']
