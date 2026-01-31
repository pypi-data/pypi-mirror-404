"""
Comprehensive tests for positional encoding and attention mechanisms

Tests all positional encoding variants and attention mechanisms
to ensure correctness and proper functionality.
"""

import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.positional_encoding import (
    # Positional Encodings
    SinusoidalPositionalEncoding,
    LearnedPositionalEmbedding,
    RelativePositionalEncoding,
    RotaryPositionalEmbedding,
    ALiBiPositionalBias,
    # Attention Mechanisms
    MultiHeadAttention,
    CausalAttention,
    scaled_dot_product_attention,
    # Utilities
    softmax,
    create_padding_mask,
    create_look_ahead_mask,
    # Aliases
    sinusoidal_pe,
    learned_pe,
    relative_pe,
    rope,
    alibi,
    mha,
    causal_attn,
    sdpa,
)


def test_sinusoidal_positional_encoding():
    """Test sinusoidal positional encoding"""
    print("Testing Sinusoidal Positional Encoding...")
    
    d_model = 512
    max_len = 100
    batch_size = 32
    seq_len = 50
    
    # Create encoding
    pe = SinusoidalPositionalEncoding(d_model, max_len)
    
    # Test forward pass
    x = np.random.randn(batch_size, seq_len, d_model)
    output = pe.forward(x)
    
    assert output.shape == x.shape, "Output shape mismatch"
    assert not np.array_equal(output, x), "Positional encoding not applied"
    
    # Test get_encoding
    positions = np.array([0, 1, 2, 3, 4])
    encodings = pe.get_encoding(positions)
    assert encodings.shape == (5, d_model), "Encoding shape mismatch"
    
    # Test uniqueness of positions
    enc_0 = pe.get_encoding(np.array([0]))
    enc_1 = pe.get_encoding(np.array([1]))
    assert not np.allclose(enc_0, enc_1), "Different positions should have different encodings"
    
    print("✓ Sinusoidal Positional Encoding tests passed")


def test_learned_positional_embedding():
    """Test learned positional embeddings"""
    print("Testing Learned Positional Embedding...")
    
    d_model = 512
    max_len = 100
    batch_size = 32
    seq_len = 50
    
    # Create embedding
    pe = LearnedPositionalEmbedding(max_len, d_model)
    
    # Test forward pass
    x = np.random.randn(batch_size, seq_len, d_model)
    output = pe.forward(x)
    
    assert output.shape == x.shape, "Output shape mismatch"
    
    # Test update
    gradients = np.random.randn(max_len, d_model) * 0.01
    old_embeddings = pe.embeddings.copy()
    pe.update_embeddings(gradients)
    assert not np.array_equal(old_embeddings, pe.embeddings), "Embeddings not updated"
    
    print("✓ Learned Positional Embedding tests passed")


def test_relative_positional_encoding():
    """Test relative positional encoding"""
    print("Testing Relative Positional Encoding...")
    
    d_model = 512
    max_relative_position = 128
    seq_len = 50
    
    # Create encoding
    pe = RelativePositionalEncoding(d_model, max_relative_position)
    
    # Test forward pass
    output = pe.forward(seq_len)
    
    assert output.shape == (seq_len, seq_len, d_model), "Output shape mismatch"
    
    # Test symmetry (relative distance should be symmetric)
    # Position i to j should have opposite encoding to j to i
    assert output.shape[0] == seq_len, "Sequence length mismatch"
    
    print("✓ Relative Positional Encoding tests passed")


def test_rotary_positional_embedding():
    """Test rotary position embedding (RoPE)"""
    print("Testing Rotary Positional Embedding (RoPE)...")
    
    d_model = 512
    max_len = 2048
    batch_size = 32
    seq_len = 50
    
    # Create RoPE
    rope_pe = RotaryPositionalEmbedding(d_model, max_len)
    
    # Test forward pass
    x = np.random.randn(batch_size, seq_len, d_model)
    output = rope_pe.forward(x)
    
    assert output.shape == x.shape, "Output shape mismatch"
    assert not np.array_equal(output, x), "RoPE not applied"
    
    # Test with specific positions
    positions = np.arange(seq_len)
    output_with_pos = rope_pe.forward(x, positions)
    assert output_with_pos.shape == x.shape, "Output shape mismatch with positions"
    
    print("✓ Rotary Positional Embedding tests passed")


def test_alibi_positional_bias():
    """Test ALiBi positional bias"""
    print("Testing ALiBi Positional Bias...")
    
    num_heads = 8
    max_len = 2048
    batch_size = 32
    seq_len = 50
    
    # Create ALiBi
    alibi_bias = ALiBiPositionalBias(num_heads, max_len)
    
    # Test forward pass
    attention_scores = np.random.randn(batch_size, num_heads, seq_len, seq_len)
    output = alibi_bias.forward(attention_scores, seq_len)
    
    assert output.shape == attention_scores.shape, "Output shape mismatch"
    assert not np.array_equal(output, attention_scores), "ALiBi bias not applied"
    
    # Test that bias increases with distance
    bias_matrix = alibi_bias.bias[0, :seq_len, :seq_len]
    # Bias should be more negative for larger distances
    assert bias_matrix[0, 0] > bias_matrix[0, seq_len-1], "Bias should decrease with distance"
    
    print("✓ ALiBi Positional Bias tests passed")


def test_scaled_dot_product_attention():
    """Test scaled dot-product attention"""
    print("Testing Scaled Dot-Product Attention...")
    
    batch_size = 32
    seq_len = 50
    d_k = 64
    d_v = 64
    
    # Create Q, K, V
    query = np.random.randn(batch_size, 1, seq_len, d_k)
    key = np.random.randn(batch_size, 1, seq_len, d_k)
    value = np.random.randn(batch_size, 1, seq_len, d_v)
    
    # Test without mask
    output, weights = scaled_dot_product_attention(query, key, value)
    
    assert output.shape == (batch_size, 1, seq_len, d_v), "Output shape mismatch"
    assert weights.shape == (batch_size, 1, seq_len, seq_len), "Weights shape mismatch"
    
    # Check attention weights sum to 1
    weights_sum = np.sum(weights, axis=-1)
    assert np.allclose(weights_sum, 1.0), "Attention weights should sum to 1"
    
    # Test with mask
    mask = np.tril(np.ones((seq_len, seq_len)))
    output_masked, weights_masked = scaled_dot_product_attention(query, key, value, mask)
    
    assert output_masked.shape == output.shape, "Masked output shape mismatch"
    
    print("✓ Scaled Dot-Product Attention tests passed")


def test_multi_head_attention():
    """Test multi-head attention"""
    print("Testing Multi-Head Attention...")
    
    d_model = 512
    num_heads = 8
    batch_size = 32
    seq_len = 50
    
    # Create MHA
    mha_layer = MultiHeadAttention(d_model, num_heads)
    
    # Test forward pass
    query = np.random.randn(batch_size, seq_len, d_model)
    key = np.random.randn(batch_size, seq_len, d_model)
    value = np.random.randn(batch_size, seq_len, d_model)
    
    output, weights = mha_layer.forward(query, key, value)
    
    assert output.shape == (batch_size, seq_len, d_model), "Output shape mismatch"
    assert weights.shape == (batch_size, num_heads, seq_len, seq_len), "Weights shape mismatch"
    
    # Test with mask
    mask = np.ones((seq_len, seq_len))
    output_masked, weights_masked = mha_layer.forward(query, key, value, mask)
    assert output_masked.shape == output.shape, "Masked output shape mismatch"
    
    print("✓ Multi-Head Attention tests passed")


def test_causal_attention():
    """Test causal (masked) attention"""
    print("Testing Causal Attention...")
    
    d_model = 512
    num_heads = 8
    batch_size = 32
    seq_len = 50
    
    # Create causal attention
    causal_attn_layer = CausalAttention(d_model, num_heads)
    
    # Test forward pass
    query = np.random.randn(batch_size, seq_len, d_model)
    key = np.random.randn(batch_size, seq_len, d_model)
    value = np.random.randn(batch_size, seq_len, d_model)
    
    output, weights = causal_attn_layer.forward(query, key, value)
    
    assert output.shape == (batch_size, seq_len, d_model), "Output shape mismatch"
    
    # Check that attention is causal (no attending to future)
    # Upper triangle of attention weights should be zero
    for h in range(num_heads):
        upper_triangle = np.triu(weights[0, h], k=1)
        assert np.allclose(upper_triangle, 0, atol=1e-5), "Attention should be causal"
    
    print("✓ Causal Attention tests passed")


def test_softmax():
    """Test softmax function"""
    print("Testing Softmax...")
    
    x = np.random.randn(32, 10)
    output = softmax(x, axis=-1)
    
    # Check shape
    assert output.shape == x.shape, "Output shape mismatch"
    
    # Check sum to 1
    sums = np.sum(output, axis=-1)
    assert np.allclose(sums, 1.0), "Softmax should sum to 1"
    
    # Check all positive
    assert np.all(output >= 0), "Softmax output should be non-negative"
    
    print("✓ Softmax tests passed")


def test_create_padding_mask():
    """Test padding mask creation"""
    print("Testing Padding Mask Creation...")
    
    seq = np.array([[1, 2, 3, 0, 0], [4, 5, 0, 0, 0]])
    mask = create_padding_mask(seq, pad_token=0)
    
    expected = np.array([[1, 1, 1, 0, 0], [1, 1, 0, 0, 0]], dtype=np.float32)
    assert np.array_equal(mask, expected), "Padding mask incorrect"
    
    print("✓ Padding Mask Creation tests passed")


def test_create_look_ahead_mask():
    """Test look-ahead mask creation"""
    print("Testing Look-Ahead Mask Creation...")
    
    size = 5
    mask = create_look_ahead_mask(size)
    
    expected = np.array([
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1]
    ])
    
    assert np.array_equal(mask, expected), "Look-ahead mask incorrect"
    
    print("✓ Look-Ahead Mask Creation tests passed")


def test_aliases():
    """Test that aliases work correctly"""
    print("Testing Aliases...")
    
    # Test positional encoding aliases
    assert sinusoidal_pe == SinusoidalPositionalEncoding
    assert learned_pe == LearnedPositionalEmbedding
    assert relative_pe == RelativePositionalEncoding
    assert rope == RotaryPositionalEmbedding
    assert alibi == ALiBiPositionalBias
    
    # Test attention aliases
    assert mha == MultiHeadAttention
    assert causal_attn == CausalAttention
    assert sdpa == scaled_dot_product_attention
    
    print("✓ Aliases tests passed")


def test_integration_transformer_block():
    """Test integration: complete transformer block"""
    print("Testing Integration: Transformer Block...")
    
    d_model = 512
    num_heads = 8
    batch_size = 32
    seq_len = 50
    
    # Create components
    pe = SinusoidalPositionalEncoding(d_model)
    mha_layer = MultiHeadAttention(d_model, num_heads)
    
    # Input
    x = np.random.randn(batch_size, seq_len, d_model)
    
    # Add positional encoding
    x_with_pe = pe.forward(x)
    
    # Apply self-attention
    output, weights = mha_layer.forward(x_with_pe, x_with_pe, x_with_pe)
    
    assert output.shape == x.shape, "Transformer block output shape mismatch"
    
    print("✓ Integration: Transformer Block tests passed")


def test_integration_gpt_style():
    """Test integration: GPT-style decoder"""
    print("Testing Integration: GPT-Style Decoder...")
    
    d_model = 512
    num_heads = 8
    batch_size = 32
    seq_len = 50
    
    # Create components
    pe = SinusoidalPositionalEncoding(d_model)
    causal_attn_layer = CausalAttention(d_model, num_heads)
    
    # Input
    x = np.random.randn(batch_size, seq_len, d_model)
    
    # Add positional encoding
    x_with_pe = pe.forward(x)
    
    # Apply causal self-attention
    output, weights = causal_attn_layer.forward(x_with_pe, x_with_pe, x_with_pe)
    
    assert output.shape == x.shape, "GPT-style decoder output shape mismatch"
    
    # Verify causality
    for h in range(num_heads):
        upper_triangle = np.triu(weights[0, h], k=1)
        assert np.allclose(upper_triangle, 0, atol=1e-5), "Should be causal"
    
    print("✓ Integration: GPT-Style Decoder tests passed")


def test_integration_rope_attention():
    """Test integration: RoPE with attention"""
    print("Testing Integration: RoPE with Attention...")
    
    d_model = 512
    num_heads = 8
    batch_size = 32
    seq_len = 50
    
    # Create components
    rope_pe = RotaryPositionalEmbedding(d_model)
    mha_layer = MultiHeadAttention(d_model, num_heads)
    
    # Input
    x = np.random.randn(batch_size, seq_len, d_model)
    
    # Apply RoPE
    x_with_rope = rope_pe.forward(x)
    
    # Apply attention
    output, weights = mha_layer.forward(x_with_rope, x_with_rope, x_with_rope)
    
    assert output.shape == x.shape, "RoPE + Attention output shape mismatch"
    
    print("✓ Integration: RoPE with Attention tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("POSITIONAL ENCODING AND ATTENTION MECHANISMS - COMPREHENSIVE TESTS")
    print("=" * 70)
    print()
    
    tests = [
        test_sinusoidal_positional_encoding,
        test_learned_positional_embedding,
        test_relative_positional_encoding,
        test_rotary_positional_embedding,
        test_alibi_positional_bias,
        test_scaled_dot_product_attention,
        test_multi_head_attention,
        test_causal_attention,
        test_softmax,
        test_create_padding_mask,
        test_create_look_ahead_mask,
        test_aliases,
        test_integration_transformer_block,
        test_integration_gpt_style,
        test_integration_rope_attention,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed_tests.append(test.__name__)
    
    print()
    print("=" * 70)
    if not failed_tests:
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  Total tests: {len(tests)}")
        print(f"  Passed: {len(tests)}")
        print(f"  Failed: 0")
        print()
        print("All positional encoding and attention mechanisms are working correctly!")
        return 0
    else:
        print("SOME TESTS FAILED! ✗")
        print("=" * 70)
        print()
        print("Failed tests:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print()
        print(f"Summary:")
        print(f"  Total tests: {len(tests)}")
        print(f"  Passed: {len(tests) - len(failed_tests)}")
        print(f"  Failed: {len(failed_tests)}")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
