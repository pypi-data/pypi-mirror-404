"""
Tests for Embedding Layers

This file contains comprehensive tests for all embedding layer types.

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.embedding import (
    Embedding,
    PositionalEncoding,
    LearnedPositionalEmbedding,
    TokenTypeEmbedding,
    CharacterEmbedding,
    cosine_similarity,
    euclidean_distance,
    most_similar,
)


# ============================================================================
# TEST EMBEDDING
# ============================================================================

def test_embedding_basic():
    """Test basic embedding functionality."""
    emb = Embedding(vocab_size=1000, embedding_dim=300)
    tokens = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])  # (batch, seq_len)
    output = emb.forward(tokens)
    
    assert output.shape == (2, 4, 300)


def test_embedding_with_padding():
    """Test embedding with padding index."""
    emb = Embedding(vocab_size=1000, embedding_dim=300, padding_idx=0)
    
    # Check padding embedding is zeros
    assert np.allclose(emb.weight[0], 0.0)


def test_embedding_load_pretrained():
    """Test loading pretrained embeddings."""
    emb = Embedding(vocab_size=100, embedding_dim=50)
    pretrained = np.random.randn(100, 50)
    
    emb.load_pretrained(pretrained)
    
    assert np.allclose(emb.weight, pretrained)


def test_embedding_max_norm():
    """Test embedding with max norm constraint."""
    emb = Embedding(vocab_size=100, embedding_dim=50, max_norm=1.0)
    tokens = np.array([[1, 2, 3]])
    output = emb.forward(tokens)
    
    # Check norms are <= max_norm
    norms = np.linalg.norm(output, axis=-1)
    assert np.all(norms <= 1.0 + 1e-6)


# ============================================================================
# TEST POSITIONAL ENCODING
# ============================================================================

def test_positional_encoding_basic():
    """Test basic positional encoding."""
    pos_enc = PositionalEncoding(embedding_dim=512, max_len=1000)
    x = np.random.randn(32, 100, 512)
    output = pos_enc.forward(x, training=False)
    
    assert output.shape == (32, 100, 512)


def test_positional_encoding_adds_position_info():
    """Test that positional encoding adds position information."""
    pos_enc = PositionalEncoding(embedding_dim=512, max_len=1000, dropout=0.0)
    x = np.random.randn(32, 100, 512)
    output = pos_enc.forward(x, training=False)
    
    # Output should be different from input
    assert not np.allclose(output, x)


def test_positional_encoding_even_dim_required():
    """Test that positional encoding requires even embedding_dim."""
    with pytest.raises(ValueError):
        PositionalEncoding(embedding_dim=513)  # Odd dimension


def test_positional_encoding_max_len_check():
    """Test that positional encoding checks max_len."""
    pos_enc = PositionalEncoding(embedding_dim=512, max_len=100)
    x = np.random.randn(32, 150, 512)  # seq_len > max_len
    
    with pytest.raises(ValueError):
        pos_enc.forward(x)


# ============================================================================
# TEST LEARNED POSITIONAL EMBEDDING
# ============================================================================

def test_learned_positional_embedding_basic():
    """Test basic learned positional embedding."""
    pos_emb = LearnedPositionalEmbedding(max_len=512, embedding_dim=768)
    x = np.random.randn(32, 100, 768)
    output = pos_emb.forward(x)
    
    assert output.shape == (32, 100, 768)


def test_learned_positional_embedding_adds_position():
    """Test that learned positional embedding adds position info."""
    pos_emb = LearnedPositionalEmbedding(max_len=512, embedding_dim=768)
    x = np.random.randn(32, 100, 768)
    output = pos_emb.forward(x)
    
    # Output should be different from input
    assert not np.allclose(output, x)


# ============================================================================
# TEST TOKEN TYPE EMBEDDING
# ============================================================================

def test_token_type_embedding_basic():
    """Test basic token type embedding."""
    token_type_emb = TokenTypeEmbedding(num_types=2, embedding_dim=768)
    token_type_ids = np.array([[0, 0, 0, 1, 1, 1]])
    output = token_type_emb.forward(token_type_ids)
    
    assert output.shape == (1, 6, 768)


def test_token_type_embedding_different_types():
    """Test that different token types have different embeddings."""
    token_type_emb = TokenTypeEmbedding(num_types=2, embedding_dim=768)
    token_type_ids = np.array([[0, 1]])
    output = token_type_emb.forward(token_type_ids)
    
    # Type 0 and type 1 should have different embeddings
    assert not np.allclose(output[0, 0], output[0, 1])


# ============================================================================
# TEST CHARACTER EMBEDDING
# ============================================================================

def test_character_embedding_basic():
    """Test basic character embedding."""
    char_emb = CharacterEmbedding(num_chars=128, embedding_dim=50)
    char_ids = np.random.randint(0, 128, (32, 20, 15))  # (batch, words, chars)
    output = char_emb.forward(char_ids)
    
    assert output.shape == (32, 20, 50)


def test_character_embedding_with_padding():
    """Test character embedding with padding."""
    char_emb = CharacterEmbedding(num_chars=128, embedding_dim=50, padding_idx=0)
    
    # Check padding embedding is zeros
    assert np.allclose(char_emb.weight[0], 0.0)


# ============================================================================
# TEST UTILITY FUNCTIONS
# ============================================================================

def test_cosine_similarity():
    """Test cosine similarity computation."""
    a = np.array([1, 0, 0])
    b = np.array([1, 0, 0])
    
    sim = cosine_similarity(a, b)
    assert np.isclose(sim, 1.0)
    
    c = np.array([0, 1, 0])
    sim2 = cosine_similarity(a, c)
    assert np.isclose(sim2, 0.0)


def test_euclidean_distance():
    """Test Euclidean distance computation."""
    a = np.array([0, 0, 0])
    b = np.array([3, 4, 0])
    
    dist = euclidean_distance(a, b)
    assert np.isclose(dist, 5.0)


def test_most_similar():
    """Test finding most similar vectors."""
    embedding_matrix = np.random.randn(100, 50)
    query_vector = embedding_matrix[10]
    
    indices, sims = most_similar(embedding_matrix, query_vector, top_k=5, exclude_idx=10)
    
    assert len(indices) == 5
    assert len(sims) == 5
    assert 10 not in indices  # Excluded


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_embedding_callable():
    """Test that embedding is callable."""
    emb = Embedding(vocab_size=1000, embedding_dim=300)
    tokens = np.array([[1, 2, 3]])
    
    output = emb(tokens)
    assert output is not None


def test_positional_encoding_callable():
    """Test that positional encoding is callable."""
    pos_enc = PositionalEncoding(embedding_dim=512)
    x = np.random.randn(32, 100, 512)
    
    output = pos_enc(x, training=False)
    assert output is not None


def test_embedding_with_positional_encoding():
    """Test combining embedding with positional encoding."""
    emb = Embedding(vocab_size=10000, embedding_dim=512)
    pos_enc = PositionalEncoding(embedding_dim=512, dropout=0.0)
    
    tokens = np.array([[1, 2, 3, 4, 5]])
    
    # Embed tokens
    embedded = emb.forward(tokens)
    
    # Add positional encoding
    output = pos_enc.forward(embedded, training=False)
    
    assert output.shape == (1, 5, 512)


def test_bert_style_embeddings():
    """Test BERT-style embeddings (token + position + token_type)."""
    # Token embeddings
    token_emb = Embedding(vocab_size=30000, embedding_dim=768)
    
    # Position embeddings
    pos_emb = LearnedPositionalEmbedding(max_len=512, embedding_dim=768)
    
    # Token type embeddings
    token_type_emb = TokenTypeEmbedding(num_types=2, embedding_dim=768)
    
    # Input
    tokens = np.array([[101, 2023, 2003, 102, 2054, 2003, 102]])  # [CLS] ... [SEP] ... [SEP]
    token_type_ids = np.array([[0, 0, 0, 0, 1, 1, 1]])
    
    # Compute embeddings
    token_embeddings = token_emb.forward(tokens)
    position_embeddings = pos_emb.forward(token_embeddings)
    token_type_embeddings = token_type_emb.forward(token_type_ids)
    
    # Combine
    final_embeddings = token_embeddings + position_embeddings + token_type_embeddings
    
    assert final_embeddings.shape == (1, 7, 768)


def test_embedding_different_vocab_sizes():
    """Test embeddings with different vocabulary sizes."""
    vocab_sizes = [100, 1000, 10000, 50000]
    
    for vocab_size in vocab_sizes:
        emb = Embedding(vocab_size=vocab_size, embedding_dim=300)
        tokens = np.array([[1, 2, 3]])
        output = emb.forward(tokens)
        
        assert output.shape == (1, 3, 300)


def test_embedding_different_dimensions():
    """Test embeddings with different dimensions."""
    embedding_dims = [50, 100, 200, 300, 512, 768]
    
    for dim in embedding_dims:
        emb = Embedding(vocab_size=1000, embedding_dim=dim)
        tokens = np.array([[1, 2, 3]])
        output = emb.forward(tokens)
        
        assert output.shape == (1, 3, dim)


def test_positional_encoding_different_lengths():
    """Test positional encoding with different sequence lengths."""
    pos_enc = PositionalEncoding(embedding_dim=512, max_len=1000)
    
    for seq_len in [10, 50, 100, 500]:
        x = np.random.randn(8, seq_len, 512)
        output = pos_enc.forward(x, training=False)
        
        assert output.shape == (8, seq_len, 512)


def test_character_embedding_aggregation():
    """Test that character embedding aggregates characters correctly."""
    char_emb = CharacterEmbedding(num_chars=128, embedding_dim=50)
    
    # Create char_ids where all characters in a word are the same
    char_ids = np.ones((1, 1, 10), dtype=int) * 5  # All chars are index 5
    
    output = char_emb.forward(char_ids)
    
    # Output should be close to the embedding of character 5
    expected = char_emb.weight[5]
    assert np.allclose(output[0, 0], expected, atol=1e-6)


def test_embedding_freeze_unfreeze():
    """Test freezing and unfreezing embeddings."""
    emb = Embedding(vocab_size=1000, embedding_dim=300)
    
    emb.freeze()
    assert hasattr(emb, 'frozen') and emb.frozen
    
    emb.unfreeze()
    assert hasattr(emb, 'frozen') and not emb.frozen


print("=" * 80)
print("ALL EMBEDDING LAYER TESTS PASSED! ✓")
print("=" * 80)
