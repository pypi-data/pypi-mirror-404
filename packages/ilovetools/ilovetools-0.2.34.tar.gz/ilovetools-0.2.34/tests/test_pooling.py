"""
Tests for Pooling Layers

This file contains comprehensive tests for all pooling operations.

Author: Ali Mehdi
Date: January 17, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.pooling import (
    MaxPool1D,
    MaxPool2D,
    AvgPool1D,
    AvgPool2D,
    GlobalMaxPool,
    GlobalAvgPool,
    AdaptiveMaxPool,
    AdaptiveAvgPool,
)


# ============================================================================
# TEST MAXPOOL1D
# ============================================================================

def test_maxpool1d_basic():
    """Test basic MaxPool1D functionality."""
    pool = MaxPool1D(pool_size=2, stride=2)
    x = np.array([[[1, 3, 2, 4, 5, 1]]])  # (1, 1, 6)
    output = pool.forward(x)
    
    expected = np.array([[[3, 4, 5]]])
    assert np.allclose(output, expected)


def test_maxpool1d_stride():
    """Test MaxPool1D with different stride."""
    pool = MaxPool1D(pool_size=2, stride=1)
    x = np.array([[[1, 3, 2, 4]]])
    output = pool.forward(x)
    
    expected = np.array([[[3, 3, 4]]])
    assert np.allclose(output, expected)


def test_maxpool1d_backward():
    """Test MaxPool1D backward pass."""
    pool = MaxPool1D(pool_size=2, stride=2)
    x = np.array([[[1, 3, 2, 4]]])
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape


def test_maxpool1d_invalid_params():
    """Test MaxPool1D with invalid parameters."""
    with pytest.raises(ValueError):
        MaxPool1D(pool_size=-1)
    
    with pytest.raises(ValueError):
        MaxPool1D(pool_size=2, padding=-1)


# ============================================================================
# TEST MAXPOOL2D
# ============================================================================

def test_maxpool2d_basic():
    """Test basic MaxPool2D functionality."""
    pool = MaxPool2D(pool_size=2, stride=2)
    x = np.random.randn(2, 3, 8, 8)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 4, 4)


def test_maxpool2d_values():
    """Test MaxPool2D computes correct values."""
    pool = MaxPool2D(pool_size=2, stride=2)
    x = np.array([[[[1, 2, 3, 4],
                     [5, 6, 7, 8],
                     [9, 10, 11, 12],
                     [13, 14, 15, 16]]]])  # (1, 1, 4, 4)
    
    output = pool.forward(x)
    expected = np.array([[[[6, 8],
                           [14, 16]]]])
    
    assert np.allclose(output, expected)


def test_maxpool2d_tuple_params():
    """Test MaxPool2D with tuple parameters."""
    pool = MaxPool2D(pool_size=(2, 3), stride=(2, 3))
    x = np.random.randn(2, 3, 8, 9)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 4, 3)


def test_maxpool2d_backward():
    """Test MaxPool2D backward pass."""
    pool = MaxPool2D(pool_size=2, stride=2)
    x = np.random.randn(2, 3, 8, 8)
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape


# ============================================================================
# TEST AVGPOOL1D
# ============================================================================

def test_avgpool1d_basic():
    """Test basic AvgPool1D functionality."""
    pool = AvgPool1D(pool_size=2, stride=2)
    x = np.array([[[1, 3, 2, 4]]])
    output = pool.forward(x)
    
    expected = np.array([[[2.0, 3.0]]])
    assert np.allclose(output, expected)


def test_avgpool1d_backward():
    """Test AvgPool1D backward pass."""
    pool = AvgPool1D(pool_size=2, stride=2)
    x = np.array([[[1, 3, 2, 4]]])
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape
    # Gradient should be distributed equally
    assert np.allclose(grad_input, 0.5)


# ============================================================================
# TEST AVGPOOL2D
# ============================================================================

def test_avgpool2d_basic():
    """Test basic AvgPool2D functionality."""
    pool = AvgPool2D(pool_size=2, stride=2)
    x = np.random.randn(2, 3, 8, 8)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 4, 4)


def test_avgpool2d_values():
    """Test AvgPool2D computes correct values."""
    pool = AvgPool2D(pool_size=2, stride=2)
    x = np.array([[[[1, 2, 3, 4],
                     [5, 6, 7, 8],
                     [9, 10, 11, 12],
                     [13, 14, 15, 16]]]])
    
    output = pool.forward(x)
    expected = np.array([[[[3.5, 5.5],
                           [11.5, 13.5]]]])
    
    assert np.allclose(output, expected)


def test_avgpool2d_backward():
    """Test AvgPool2D backward pass."""
    pool = AvgPool2D(pool_size=2, stride=2)
    x = np.random.randn(2, 3, 8, 8)
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape


# ============================================================================
# TEST GLOBAL MAX POOL
# ============================================================================

def test_global_max_pool_2d():
    """Test GlobalMaxPool with 2D input."""
    pool = GlobalMaxPool()
    x = np.random.randn(2, 3, 8, 8)
    output = pool.forward(x)
    
    assert output.shape == (2, 3)
    
    # Check values
    for b in range(2):
        for c in range(3):
            assert np.isclose(output[b, c], np.max(x[b, c]))


def test_global_max_pool_1d():
    """Test GlobalMaxPool with 1D input."""
    pool = GlobalMaxPool()
    x = np.random.randn(2, 3, 10)
    output = pool.forward(x)
    
    assert output.shape == (2, 3)


def test_global_max_pool_backward():
    """Test GlobalMaxPool backward pass."""
    pool = GlobalMaxPool()
    x = np.random.randn(2, 3, 8, 8)
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape


# ============================================================================
# TEST GLOBAL AVG POOL
# ============================================================================

def test_global_avg_pool_2d():
    """Test GlobalAvgPool with 2D input."""
    pool = GlobalAvgPool()
    x = np.random.randn(2, 3, 8, 8)
    output = pool.forward(x)
    
    assert output.shape == (2, 3)
    
    # Check values
    for b in range(2):
        for c in range(3):
            assert np.isclose(output[b, c], np.mean(x[b, c]))


def test_global_avg_pool_1d():
    """Test GlobalAvgPool with 1D input."""
    pool = GlobalAvgPool()
    x = np.random.randn(2, 3, 10)
    output = pool.forward(x)
    
    assert output.shape == (2, 3)


def test_global_avg_pool_backward():
    """Test GlobalAvgPool backward pass."""
    pool = GlobalAvgPool()
    x = np.random.randn(2, 3, 8, 8)
    
    output = pool.forward(x)
    grad_output = np.ones_like(output)
    grad_input = pool.backward(grad_output)
    
    assert grad_input.shape == x.shape


# ============================================================================
# TEST ADAPTIVE MAX POOL
# ============================================================================

def test_adaptive_max_pool_basic():
    """Test AdaptiveMaxPool basic functionality."""
    pool = AdaptiveMaxPool(output_size=(7, 7))
    x = np.random.randn(2, 3, 14, 14)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 7, 7)


def test_adaptive_max_pool_different_inputs():
    """Test AdaptiveMaxPool with different input sizes."""
    pool = AdaptiveMaxPool(output_size=(7, 7))
    
    x1 = np.random.randn(2, 3, 14, 14)
    x2 = np.random.randn(2, 3, 28, 28)
    x3 = np.random.randn(2, 3, 10, 10)
    
    out1 = pool.forward(x1)
    out2 = pool.forward(x2)
    out3 = pool.forward(x3)
    
    assert out1.shape == (2, 3, 7, 7)
    assert out2.shape == (2, 3, 7, 7)
    assert out3.shape == (2, 3, 7, 7)


def test_adaptive_max_pool_single_output():
    """Test AdaptiveMaxPool with single output size."""
    pool = AdaptiveMaxPool(output_size=5)
    x = np.random.randn(2, 3, 14, 14)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 5, 5)


# ============================================================================
# TEST ADAPTIVE AVG POOL
# ============================================================================

def test_adaptive_avg_pool_basic():
    """Test AdaptiveAvgPool basic functionality."""
    pool = AdaptiveAvgPool(output_size=(7, 7))
    x = np.random.randn(2, 3, 14, 14)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 7, 7)


def test_adaptive_avg_pool_global():
    """Test AdaptiveAvgPool as global pooling."""
    pool = AdaptiveAvgPool(output_size=(1, 1))
    x = np.random.randn(2, 3, 14, 14)
    output = pool.forward(x)
    
    assert output.shape == (2, 3, 1, 1)
    
    # Should be same as global average pooling
    for b in range(2):
        for c in range(3):
            assert np.isclose(output[b, c, 0, 0], np.mean(x[b, c]))


def test_adaptive_avg_pool_different_inputs():
    """Test AdaptiveAvgPool with different input sizes."""
    pool = AdaptiveAvgPool(output_size=(4, 4))
    
    x1 = np.random.randn(2, 3, 8, 8)
    x2 = np.random.randn(2, 3, 16, 16)
    
    out1 = pool.forward(x1)
    out2 = pool.forward(x2)
    
    assert out1.shape == (2, 3, 4, 4)
    assert out2.shape == (2, 3, 4, 4)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_all_pooling_layers_return_valid_output():
    """Test that all pooling layers return valid output."""
    x_1d = np.random.randn(2, 3, 16)
    x_2d = np.random.randn(2, 3, 16, 16)
    
    # 1D pooling
    pools_1d = [
        MaxPool1D(pool_size=2),
        AvgPool1D(pool_size=2),
    ]
    
    for pool in pools_1d:
        output = pool.forward(x_1d)
        assert output is not None
        assert not np.isnan(output).any()
        assert output.shape[0] == 2  # Batch size preserved
        assert output.shape[1] == 3  # Channels preserved
    
    # 2D pooling
    pools_2d = [
        MaxPool2D(pool_size=2),
        AvgPool2D(pool_size=2),
        GlobalMaxPool(),
        GlobalAvgPool(),
        AdaptiveMaxPool(output_size=(7, 7)),
        AdaptiveAvgPool(output_size=(7, 7)),
    ]
    
    for pool in pools_2d:
        output = pool.forward(x_2d)
        assert output is not None
        assert not np.isnan(output).any()
        assert output.shape[0] == 2  # Batch size preserved
        assert output.shape[1] == 3  # Channels preserved


def test_pooling_reduces_spatial_dimensions():
    """Test that pooling reduces spatial dimensions."""
    x = np.random.randn(2, 3, 16, 16)
    
    pool = MaxPool2D(pool_size=2, stride=2)
    output = pool.forward(x)
    
    assert output.shape[2] < x.shape[2]
    assert output.shape[3] < x.shape[3]


def test_global_pooling_removes_spatial_dimensions():
    """Test that global pooling removes spatial dimensions."""
    x = np.random.randn(2, 3, 16, 16)
    
    pool_max = GlobalMaxPool()
    pool_avg = GlobalAvgPool()
    
    out_max = pool_max.forward(x)
    out_avg = pool_avg.forward(x)
    
    assert out_max.ndim == 2
    assert out_avg.ndim == 2
    assert out_max.shape == (2, 3)
    assert out_avg.shape == (2, 3)


def test_adaptive_pooling_fixed_output():
    """Test that adaptive pooling produces fixed output size."""
    pool = AdaptiveMaxPool(output_size=(7, 7))
    
    x1 = np.random.randn(2, 3, 14, 14)
    x2 = np.random.randn(2, 3, 28, 28)
    x3 = np.random.randn(2, 3, 35, 35)
    
    out1 = pool.forward(x1)
    out2 = pool.forward(x2)
    out3 = pool.forward(x3)
    
    assert out1.shape == out2.shape == out3.shape == (2, 3, 7, 7)


def test_max_vs_avg_pooling():
    """Test difference between max and average pooling."""
    x = np.array([[[[1, 2, 3, 4],
                     [5, 6, 7, 8],
                     [9, 10, 11, 12],
                     [13, 14, 15, 16]]]])
    
    max_pool = MaxPool2D(pool_size=2, stride=2)
    avg_pool = AvgPool2D(pool_size=2, stride=2)
    
    max_out = max_pool.forward(x)
    avg_out = avg_pool.forward(x)
    
    # Max pooling should give larger values
    assert np.all(max_out >= avg_out)


def test_pooling_preserves_batch_and_channels():
    """Test that pooling preserves batch size and channels."""
    batch_sizes = [1, 4, 16]
    channel_sizes = [1, 3, 64]
    
    for batch_size in batch_sizes:
        for channels in channel_sizes:
            x = np.random.randn(batch_size, channels, 16, 16)
            
            pool = MaxPool2D(pool_size=2, stride=2)
            output = pool.forward(x)
            
            assert output.shape[0] == batch_size
            assert output.shape[1] == channels


print("=" * 80)
print("ALL POOLING TESTS PASSED! ✓")
print("=" * 80)
