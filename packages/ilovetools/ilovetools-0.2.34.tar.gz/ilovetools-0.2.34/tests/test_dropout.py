"""
Comprehensive Tests for Dropout Regularization

Tests all dropout variants with various scenarios and edge cases.

Author: Ali Mehdi
Date: January 12, 2026
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.dropout import (
    Dropout,
    SpatialDropout2D,
    SpatialDropout3D,
    VariationalDropout,
    DropConnect,
    AlphaDropout,
    dropout,
    spatial_dropout_2d,
    spatial_dropout_3d,
    variational_dropout,
    dropconnect,
    alpha_dropout,
)


def test_standard_dropout_basic():
    """Test basic standard dropout functionality."""
    print("Testing standard dropout basic...")
    
    drop = Dropout(rate=0.5, seed=42)
    x = np.ones((10, 20))
    
    # Training mode
    x_train = drop(x, training=True)
    assert x_train.shape == x.shape
    assert not np.allclose(x_train, x)  # Should be different
    assert np.any(x_train == 0)  # Should have zeros
    
    # Inference mode
    x_test = drop(x, training=False)
    assert np.allclose(x_test, x)  # Should be unchanged
    
    print("✓ Standard dropout basic test passed")


def test_standard_dropout_scaling():
    """Test that dropout properly scales activations."""
    print("Testing dropout scaling...")
    
    drop = Dropout(rate=0.5, seed=42)
    x = np.ones((1000, 100))
    
    x_dropped = drop(x, training=True)
    
    # Mean should be approximately preserved
    assert abs(np.mean(x_dropped) - 1.0) < 0.1
    
    print("✓ Dropout scaling test passed")


def test_dropout_rate_zero():
    """Test dropout with rate=0 (no dropout)."""
    print("Testing dropout with rate=0...")
    
    drop = Dropout(rate=0.0, seed=42)
    x = np.random.randn(10, 20)
    
    x_dropped = drop(x, training=True)
    assert np.allclose(x_dropped, x)
    
    print("✓ Dropout rate=0 test passed")


def test_dropout_reproducibility():
    """Test that dropout is reproducible with same seed."""
    print("Testing dropout reproducibility...")
    
    x = np.random.randn(10, 20)
    
    drop1 = Dropout(rate=0.5, seed=42)
    drop2 = Dropout(rate=0.5, seed=42)
    
    x1 = drop1(x, training=True)
    x2 = drop2(x, training=True)
    
    assert np.allclose(x1, x2)
    
    print("✓ Dropout reproducibility test passed")


def test_dropout_different_seeds():
    """Test that different seeds produce different results."""
    print("Testing dropout with different seeds...")
    
    x = np.random.randn(10, 20)
    
    drop1 = Dropout(rate=0.5, seed=42)
    drop2 = Dropout(rate=0.5, seed=123)
    
    x1 = drop1(x, training=True)
    x2 = drop2(x, training=True)
    
    assert not np.allclose(x1, x2)
    
    print("✓ Dropout different seeds test passed")


def test_spatial_dropout_2d_basic():
    """Test basic spatial dropout 2D functionality."""
    print("Testing spatial dropout 2D basic...")
    
    drop = SpatialDropout2D(rate=0.5, data_format='channels_first', seed=42)
    x = np.ones((4, 8, 16, 16))  # (batch, channels, height, width)
    
    x_dropped = drop(x, training=True)
    
    assert x_dropped.shape == x.shape
    
    # Check that entire feature maps are dropped
    for b in range(x_dropped.shape[0]):
        for c in range(x_dropped.shape[1]):
            feature_map = x_dropped[b, c]
            # Feature map should be either all zeros or all scaled
            unique_vals = np.unique(feature_map)
            assert len(unique_vals) <= 2  # Either 0 or scaled value
    
    print("✓ Spatial dropout 2D basic test passed")


def test_spatial_dropout_2d_channels_last():
    """Test spatial dropout 2D with channels_last format."""
    print("Testing spatial dropout 2D channels_last...")
    
    drop = SpatialDropout2D(rate=0.5, data_format='channels_last', seed=42)
    x = np.ones((4, 16, 16, 8))  # (batch, height, width, channels)
    
    x_dropped = drop(x, training=True)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Spatial dropout 2D channels_last test passed")


def test_spatial_dropout_3d_basic():
    """Test basic spatial dropout 3D functionality."""
    print("Testing spatial dropout 3D basic...")
    
    drop = SpatialDropout3D(rate=0.5, data_format='channels_first', seed=42)
    x = np.ones((2, 4, 8, 16, 16))  # (batch, channels, depth, height, width)
    
    x_dropped = drop(x, training=True)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Spatial dropout 3D basic test passed")


def test_variational_dropout_basic():
    """Test basic variational dropout functionality."""
    print("Testing variational dropout basic...")
    
    drop = VariationalDropout(rate=0.5, seed=42)
    x = np.ones((4, 10, 32))  # (batch, time_steps, features)
    
    x_dropped = drop(x, training=True)
    
    assert x_dropped.shape == x.shape
    
    # Check that same mask is applied across time steps
    for b in range(x_dropped.shape[0]):
        for f in range(x_dropped.shape[2]):
            # All time steps should have same dropout pattern for each feature
            time_series = x_dropped[b, :, f]
            if np.any(time_series == 0):
                assert np.all(time_series == 0)  # All or none
    
    print("✓ Variational dropout basic test passed")


def test_dropconnect_basic():
    """Test basic DropConnect functionality."""
    print("Testing DropConnect basic...")
    
    drop = DropConnect(rate=0.5, seed=42)
    x = np.random.randn(8, 16)
    weights = np.random.randn(16, 32)
    
    # Training mode
    output_train = drop.apply(x, weights, training=True)
    assert output_train.shape == (8, 32)
    
    # Inference mode
    output_test = drop.apply(x, weights, training=False)
    assert output_test.shape == (8, 32)
    assert np.allclose(output_test, np.dot(x, weights))
    
    print("✓ DropConnect basic test passed")


def test_dropconnect_mask():
    """Test DropConnect mask generation."""
    print("Testing DropConnect mask...")
    
    drop = DropConnect(rate=0.5, seed=42)
    mask = drop.get_mask((100, 50))
    
    assert mask.shape == (100, 50)
    assert np.all((mask == 0) | (mask == 1))
    
    # Check dropout rate
    zero_fraction = np.sum(mask == 0) / mask.size
    assert abs(zero_fraction - 0.5) < 0.1
    
    print("✓ DropConnect mask test passed")


def test_alpha_dropout_basic():
    """Test basic alpha dropout functionality."""
    print("Testing alpha dropout basic...")
    
    drop = AlphaDropout(rate=0.1, seed=42)
    x = np.random.randn(100, 50)
    
    x_dropped = drop(x, training=True)
    
    assert x_dropped.shape == x.shape
    
    # Alpha dropout should preserve mean and variance approximately
    assert abs(np.mean(x_dropped) - np.mean(x)) < 0.5
    assert abs(np.std(x_dropped) - np.std(x)) < 0.5
    
    print("✓ Alpha dropout basic test passed")


def test_alpha_dropout_selu_compatibility():
    """Test alpha dropout with SELU activation."""
    print("Testing alpha dropout SELU compatibility...")
    
    # SELU activation
    alpha = 1.6732632423543772848170429916717
    scale = 1.0507009873554804934193349852946
    
    def selu(x):
        return scale * np.where(x > 0, x, alpha * (np.exp(x) - 1))
    
    drop = AlphaDropout(rate=0.1, seed=42)
    x = np.random.randn(1000, 100)
    
    # Apply SELU then alpha dropout
    x_selu = selu(x)
    x_dropped = drop(x_selu, training=True)
    
    # Mean and variance should be approximately preserved
    assert abs(np.mean(x_dropped)) < 0.5
    assert abs(np.std(x_dropped) - 1.0) < 0.5
    
    print("✓ Alpha dropout SELU compatibility test passed")


def test_dropout_function():
    """Test dropout convenience function."""
    print("Testing dropout convenience function...")
    
    x = np.ones((10, 20))
    x_dropped = dropout(x, rate=0.5, training=True, seed=42)
    
    assert x_dropped.shape == x.shape
    assert not np.allclose(x_dropped, x)
    
    print("✓ Dropout function test passed")


def test_spatial_dropout_2d_function():
    """Test spatial_dropout_2d convenience function."""
    print("Testing spatial_dropout_2d function...")
    
    x = np.ones((4, 8, 16, 16))
    x_dropped = spatial_dropout_2d(x, rate=0.5, training=True, seed=42)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Spatial dropout 2D function test passed")


def test_spatial_dropout_3d_function():
    """Test spatial_dropout_3d convenience function."""
    print("Testing spatial_dropout_3d function...")
    
    x = np.ones((2, 4, 8, 16, 16))
    x_dropped = spatial_dropout_3d(x, rate=0.5, training=True, seed=42)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Spatial dropout 3D function test passed")


def test_variational_dropout_function():
    """Test variational_dropout convenience function."""
    print("Testing variational_dropout function...")
    
    x = np.ones((4, 10, 32))
    x_dropped = variational_dropout(x, rate=0.5, training=True, seed=42)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Variational dropout function test passed")


def test_dropconnect_function():
    """Test dropconnect convenience function."""
    print("Testing dropconnect function...")
    
    x = np.random.randn(8, 16)
    weights = np.random.randn(16, 32)
    output = dropconnect(x, weights, rate=0.5, training=True, seed=42)
    
    assert output.shape == (8, 32)
    
    print("✓ DropConnect function test passed")


def test_alpha_dropout_function():
    """Test alpha_dropout convenience function."""
    print("Testing alpha_dropout function...")
    
    x = np.random.randn(100, 50)
    x_dropped = alpha_dropout(x, rate=0.1, training=True, seed=42)
    
    assert x_dropped.shape == x.shape
    
    print("✓ Alpha dropout function test passed")


def test_dropout_invalid_rate():
    """Test dropout with invalid rate."""
    print("Testing dropout with invalid rate...")
    
    try:
        drop = Dropout(rate=1.5)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    try:
        drop = Dropout(rate=-0.1)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Dropout invalid rate test passed")


def test_spatial_dropout_invalid_input():
    """Test spatial dropout with invalid input shape."""
    print("Testing spatial dropout with invalid input...")
    
    drop = SpatialDropout2D(rate=0.5)
    x = np.ones((10, 20))  # 2D instead of 4D
    
    try:
        x_dropped = drop(x, training=True)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Spatial dropout invalid input test passed")


def test_variational_dropout_invalid_input():
    """Test variational dropout with invalid input shape."""
    print("Testing variational dropout with invalid input...")
    
    drop = VariationalDropout(rate=0.5)
    x = np.ones((10, 20))  # 2D instead of 3D
    
    try:
        x_dropped = drop(x, training=True)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Variational dropout invalid input test passed")


def test_dropout_integration():
    """Test dropout in a simple neural network."""
    print("Testing dropout integration...")
    
    # Simple 2-layer network
    batch_size = 32
    input_dim = 100
    hidden_dim = 50
    output_dim = 10
    
    # Initialize weights
    W1 = np.random.randn(input_dim, hidden_dim) * 0.01
    W2 = np.random.randn(hidden_dim, output_dim) * 0.01
    
    # Input
    x = np.random.randn(batch_size, input_dim)
    
    # Forward pass with dropout
    drop = Dropout(rate=0.5, seed=42)
    
    h1 = np.maximum(0, np.dot(x, W1))  # ReLU
    h1_dropped = drop(h1, training=True)
    output = np.dot(h1_dropped, W2)
    
    assert output.shape == (batch_size, output_dim)
    
    print("✓ Dropout integration test passed")


def run_all_tests():
    """Run all dropout tests."""
    print("=" * 80)
    print("RUNNING DROPOUT REGULARIZATION TESTS")
    print("=" * 80)
    print()
    
    tests = [
        test_standard_dropout_basic,
        test_standard_dropout_scaling,
        test_dropout_rate_zero,
        test_dropout_reproducibility,
        test_dropout_different_seeds,
        test_spatial_dropout_2d_basic,
        test_spatial_dropout_2d_channels_last,
        test_spatial_dropout_3d_basic,
        test_variational_dropout_basic,
        test_dropconnect_basic,
        test_dropconnect_mask,
        test_alpha_dropout_basic,
        test_alpha_dropout_selu_compatibility,
        test_dropout_function,
        test_spatial_dropout_2d_function,
        test_spatial_dropout_3d_function,
        test_variational_dropout_function,
        test_dropconnect_function,
        test_alpha_dropout_function,
        test_dropout_invalid_rate,
        test_spatial_dropout_invalid_input,
        test_variational_dropout_invalid_input,
        test_dropout_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
