"""
Test script to verify normalization module imports and basic functionality
Run this after installing from PyPI to ensure everything works correctly
"""

import sys

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        from ilovetools.ml.normalization import (
            # Classes
            BatchNorm1d,
            BatchNorm2d,
            LayerNorm,
            GroupNorm,
            InstanceNorm,
            # Functional API
            batch_norm_1d,
            layer_norm,
            group_norm,
            instance_norm,
            # Aliases
            batchnorm1d,
            layernorm,
            groupnorm,
            instancenorm,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of normalization classes"""
    print("\nTesting basic functionality...")
    
    try:
        import numpy as np
        from ilovetools.ml.normalization import BatchNorm1d, LayerNorm
        
        # Test BatchNorm1d
        bn = BatchNorm1d(num_features=128)
        x = np.random.randn(32, 128)
        output = bn.forward(x, training=True)
        assert output.shape == x.shape, "BatchNorm1d output shape mismatch"
        print("✓ BatchNorm1d works correctly")
        
        # Test LayerNorm
        ln = LayerNorm(normalized_shape=512)
        x = np.random.randn(32, 10, 512)
        output = ln.forward(x)
        assert output.shape == x.shape, "LayerNorm output shape mismatch"
        print("✓ LayerNorm works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False


def test_functional_api():
    """Test functional API"""
    print("\nTesting functional API...")
    
    try:
        import numpy as np
        from ilovetools.ml.normalization import batch_norm_1d, layer_norm
        
        # Test batch_norm_1d
        x = np.random.randn(32, 128)
        gamma = np.ones(128)
        beta = np.zeros(128)
        running_mean = np.zeros(128)
        running_var = np.ones(128)
        
        output, _, _ = batch_norm_1d(x, gamma, beta, running_mean, running_var, training=True)
        assert output.shape == x.shape, "batch_norm_1d output shape mismatch"
        print("✓ batch_norm_1d works correctly")
        
        # Test layer_norm
        x = np.random.randn(32, 10, 512)
        gamma = np.ones(512)
        beta = np.zeros(512)
        
        output = layer_norm(x, gamma, beta)
        assert output.shape == x.shape, "layer_norm output shape mismatch"
        print("✓ layer_norm works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Functional API test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ILOVETOOLS NORMALIZATION MODULE - INSTALLATION TEST")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(test_imports())
    
    # Test basic functionality
    results.append(test_basic_functionality())
    
    # Test functional API
    results.append(test_functional_api())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nThe normalization module is correctly installed and working!")
        print("\nYou can now use:")
        print("  from ilovetools.ml.normalization import BatchNorm1d, LayerNorm")
        return 0
    else:
        print("SOME TESTS FAILED! ✗")
        print("=" * 60)
        print("\nPlease check the errors above and ensure:")
        print("  1. ilovetools is installed: pip install ilovetools")
        print("  2. numpy is installed: pip install numpy")
        return 1


if __name__ == "__main__":
    sys.exit(main())
