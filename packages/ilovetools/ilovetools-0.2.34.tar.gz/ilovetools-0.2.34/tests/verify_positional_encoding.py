"""
Verification script for positional encoding and attention mechanisms
Tests that all imports work correctly and basic functionality is accessible
"""

import sys

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports from ilovetools.ml.positional_encoding...")
    
    try:
        from ilovetools.ml.positional_encoding import (
            # Positional Encoding Classes
            SinusoidalPositionalEncoding,
            LearnedPositionalEmbedding,
            RelativePositionalEncoding,
            RotaryPositionalEmbedding,
            ALiBiPositionalBias,
            # Attention Classes
            MultiHeadAttention,
            CausalAttention,
            # Attention Functions
            scaled_dot_product_attention,
            # Utility Functions
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
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        import numpy as np
        from ilovetools.ml.positional_encoding import (
            SinusoidalPositionalEncoding,
            MultiHeadAttention,
            RotaryPositionalEmbedding,
            ALiBiPositionalBias,
        )
        
        # Test Sinusoidal PE
        pe = SinusoidalPositionalEncoding(d_model=512, max_len=100)
        x = np.random.randn(32, 50, 512)
        output = pe.forward(x)
        assert output.shape == x.shape, "Sinusoidal PE output shape mismatch"
        print("✓ Sinusoidal Positional Encoding works")
        
        # Test Multi-Head Attention
        mha = MultiHeadAttention(d_model=512, num_heads=8)
        q = np.random.randn(32, 50, 512)
        k = np.random.randn(32, 50, 512)
        v = np.random.randn(32, 50, 512)
        output, weights = mha.forward(q, k, v)
        assert output.shape == q.shape, "MHA output shape mismatch"
        print("✓ Multi-Head Attention works")
        
        # Test RoPE
        rope_pe = RotaryPositionalEmbedding(d_model=512, max_len=2048)
        output_rope = rope_pe.forward(x)
        assert output_rope.shape == x.shape, "RoPE output shape mismatch"
        print("✓ Rotary Position Embedding works")
        
        # Test ALiBi
        alibi_bias = ALiBiPositionalBias(num_heads=8, max_len=2048)
        scores = np.random.randn(32, 8, 50, 50)
        output_alibi = alibi_bias.forward(scores, 50)
        assert output_alibi.shape == scores.shape, "ALiBi output shape mismatch"
        print("✓ ALiBi Positional Bias works")
        
        return True
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False


def test_aliases():
    """Test that aliases work"""
    print("\nTesting aliases...")
    
    try:
        from ilovetools.ml.positional_encoding import (
            SinusoidalPositionalEncoding,
            sinusoidal_pe,
            MultiHeadAttention,
            mha,
            RotaryPositionalEmbedding,
            rope,
        )
        
        assert sinusoidal_pe == SinusoidalPositionalEncoding
        assert mha == MultiHeadAttention
        assert rope == RotaryPositionalEmbedding
        
        print("✓ All aliases work correctly")
        return True
    except Exception as e:
        print(f"✗ Alias test failed: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 70)
    print("POSITIONAL ENCODING & ATTENTION - IMPORT VERIFICATION")
    print("=" * 70)
    print()
    
    results = []
    
    # Test imports
    results.append(test_imports())
    
    # Test basic functionality
    results.append(test_basic_functionality())
    
    # Test aliases
    results.append(test_aliases())
    
    # Summary
    print("\n" + "=" * 70)
    if all(results):
        print("ALL VERIFICATION TESTS PASSED! ✓")
        print("=" * 70)
        print("\nThe positional encoding and attention module is correctly installed!")
        print("\nYou can now use:")
        print("  from ilovetools.ml.positional_encoding import (")
        print("      SinusoidalPositionalEncoding,")
        print("      MultiHeadAttention,")
        print("      RotaryPositionalEmbedding,")
        print("      ALiBiPositionalBias,")
        print("      CausalAttention,")
        print("  )")
        return 0
    else:
        print("SOME TESTS FAILED! ✗")
        print("=" * 70)
        print("\nPlease check the errors above and ensure:")
        print("  1. ilovetools is installed: pip install ilovetools")
        print("  2. numpy is installed: pip install numpy")
        return 1


if __name__ == "__main__":
    sys.exit(main())
