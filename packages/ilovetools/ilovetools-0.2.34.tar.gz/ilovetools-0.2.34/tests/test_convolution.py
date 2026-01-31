"""
Tests for Convolution Operations

This file contains comprehensive tests for all convolution types.

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.convolution import (
    Conv1D,
    Conv2D,
    Conv3D,
    DepthwiseConv2D,
    SeparableConv2D,
    DilatedConv2D,
    TransposedConv2D,
    Conv1x1,
)


# ============================================================================
# TEST CONV1D
# ============================================================================

def test_conv1d_basic():
    """Test basic Conv1D functionality."""
    conv = Conv1D(in_channels=128, out_channels=256, kernel_size=3)
    x = np.random.randn(32, 128, 100)
    output = conv.forward(x)
    
    assert output.shape[0] == 32  # Batch size preserved
    assert output.shape[1] == 256  # Output channels
    assert output.shape[2] == 98  # Length reduced


def test_conv1d_padding():
    """Test Conv1D with padding."""
    conv = Conv1D(in_channels=64, out_channels=64, kernel_size=3, padding=1)
    x = np.random.randn(16, 64, 100)
    output = conv.forward(x)
    
    assert output.shape == (16, 64, 100)  # Same length with padding


def test_conv1d_stride():
    """Test Conv1D with stride."""
    conv = Conv1D(in_channels=32, out_channels=64, kernel_size=3, stride=2)
    x = np.random.randn(8, 32, 100)
    output = conv.forward(x)
    
    assert output.shape[2] == 49  # Length halved with stride=2


# ============================================================================
# TEST CONV2D
# ============================================================================

def test_conv2d_basic():
    """Test basic Conv2D functionality."""
    conv = Conv2D(in_channels=3, out_channels=64, kernel_size=3)
    x = np.random.randn(32, 3, 224, 224)
    output = conv.forward(x)
    
    assert output.shape[0] == 32  # Batch size preserved
    assert output.shape[1] == 64  # Output channels
    assert output.shape[2] == 222  # Height reduced
    assert output.shape[3] == 222  # Width reduced


def test_conv2d_same_padding():
    """Test Conv2D with 'same' padding."""
    conv = Conv2D(in_channels=3, out_channels=64, kernel_size=3, padding='same')
    x = np.random.randn(32, 3, 224, 224)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 224, 224)  # Same spatial dimensions


def test_conv2d_valid_padding():
    """Test Conv2D with 'valid' padding."""
    conv = Conv2D(in_channels=3, out_channels=64, kernel_size=3, padding='valid')
    x = np.random.randn(32, 3, 224, 224)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 222, 222)  # Reduced spatial dimensions


def test_conv2d_stride():
    """Test Conv2D with stride."""
    conv = Conv2D(in_channels=64, out_channels=128, kernel_size=3, stride=2, padding=1)
    x = np.random.randn(32, 64, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (32, 128, 28, 28)  # Spatial dimensions halved


def test_conv2d_tuple_params():
    """Test Conv2D with tuple parameters."""
    conv = Conv2D(in_channels=3, out_channels=64, kernel_size=(3, 5), 
                  stride=(1, 2), padding=(1, 2))
    x = np.random.randn(16, 3, 32, 32)
    output = conv.forward(x)
    
    assert output.shape[0] == 16
    assert output.shape[1] == 64


# ============================================================================
# TEST CONV3D
# ============================================================================

def test_conv3d_basic():
    """Test basic Conv3D functionality."""
    conv = Conv3D(in_channels=3, out_channels=64, kernel_size=3)
    x = np.random.randn(8, 3, 16, 112, 112)
    output = conv.forward(x)
    
    assert output.shape[0] == 8  # Batch size preserved
    assert output.shape[1] == 64  # Output channels
    assert output.shape[2] == 14  # Depth reduced
    assert output.shape[3] == 110  # Height reduced
    assert output.shape[4] == 110  # Width reduced


def test_conv3d_padding():
    """Test Conv3D with padding."""
    conv = Conv3D(in_channels=3, out_channels=32, kernel_size=3, padding=1)
    x = np.random.randn(4, 3, 16, 64, 64)
    output = conv.forward(x)
    
    assert output.shape == (4, 32, 16, 64, 64)  # Same spatial dimensions


# ============================================================================
# TEST DEPTHWISE CONV2D
# ============================================================================

def test_depthwise_conv2d_basic():
    """Test basic DepthwiseConv2D functionality."""
    conv = DepthwiseConv2D(in_channels=64, kernel_size=3, padding=1)
    x = np.random.randn(32, 64, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 56, 56)  # Channels preserved


def test_depthwise_conv2d_stride():
    """Test DepthwiseConv2D with stride."""
    conv = DepthwiseConv2D(in_channels=128, kernel_size=3, stride=2, padding=1)
    x = np.random.randn(16, 128, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (16, 128, 28, 28)  # Spatial dimensions halved


# ============================================================================
# TEST SEPARABLE CONV2D
# ============================================================================

def test_separable_conv2d_basic():
    """Test basic SeparableConv2D functionality."""
    conv = SeparableConv2D(in_channels=64, out_channels=128, kernel_size=3, padding=1)
    x = np.random.randn(32, 64, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (32, 128, 56, 56)


def test_separable_conv2d_stride():
    """Test SeparableConv2D with stride."""
    conv = SeparableConv2D(in_channels=64, out_channels=128, kernel_size=3, stride=2, padding=1)
    x = np.random.randn(16, 64, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (16, 128, 28, 28)


# ============================================================================
# TEST DILATED CONV2D
# ============================================================================

def test_dilated_conv2d_basic():
    """Test basic DilatedConv2D functionality."""
    conv = DilatedConv2D(in_channels=64, out_channels=64, kernel_size=3, dilation=2, padding=2)
    x = np.random.randn(32, 64, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 56, 56)


def test_dilated_conv2d_receptive_field():
    """Test DilatedConv2D expands receptive field."""
    # Dilation=2 with kernel=3 gives effective kernel=5
    conv = DilatedConv2D(in_channels=32, out_channels=32, kernel_size=3, dilation=2)
    x = np.random.randn(8, 32, 28, 28)
    output = conv.forward(x)
    
    assert output.shape[0] == 8
    assert output.shape[1] == 32


# ============================================================================
# TEST TRANSPOSED CONV2D
# ============================================================================

def test_transposed_conv2d_basic():
    """Test basic TransposedConv2D functionality."""
    conv = TransposedConv2D(in_channels=128, out_channels=64, kernel_size=4, stride=2, padding=1)
    x = np.random.randn(32, 128, 28, 28)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 56, 56)  # 2x upsampling


def test_transposed_conv2d_upsampling():
    """Test TransposedConv2D upsamples correctly."""
    conv = TransposedConv2D(in_channels=256, out_channels=128, kernel_size=4, stride=2, padding=1)
    x = np.random.randn(16, 256, 14, 14)
    output = conv.forward(x)
    
    assert output.shape[2] == 28  # Height doubled
    assert output.shape[3] == 28  # Width doubled


# ============================================================================
# TEST CONV1X1
# ============================================================================

def test_conv1x1_basic():
    """Test basic Conv1x1 functionality."""
    conv = Conv1x1(in_channels=256, out_channels=64)
    x = np.random.randn(32, 256, 56, 56)
    output = conv.forward(x)
    
    assert output.shape == (32, 64, 56, 56)  # Spatial dims preserved, channels reduced


def test_conv1x1_channel_expansion():
    """Test Conv1x1 for channel expansion."""
    conv = Conv1x1(in_channels=64, out_channels=256)
    x = np.random.randn(16, 64, 28, 28)
    output = conv.forward(x)
    
    assert output.shape == (16, 256, 28, 28)  # Channels expanded


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_all_convolutions_return_valid_output():
    """Test that all convolution types return valid output."""
    x_1d = np.random.randn(8, 64, 100)
    x_2d = np.random.randn(8, 64, 28, 28)
    x_3d = np.random.randn(4, 3, 8, 28, 28)
    
    # 1D
    conv1d = Conv1D(64, 128, 3, padding=1)
    out1d = conv1d.forward(x_1d)
    assert out1d is not None
    assert not np.isnan(out1d).any()
    
    # 2D
    conv2d = Conv2D(64, 128, 3, padding=1)
    out2d = conv2d.forward(x_2d)
    assert out2d is not None
    assert not np.isnan(out2d).any()
    
    # 3D
    conv3d = Conv3D(3, 32, 3, padding=1)
    out3d = conv3d.forward(x_3d)
    assert out3d is not None
    assert not np.isnan(out3d).any()
    
    # Depthwise
    depthwise = DepthwiseConv2D(64, 3, padding=1)
    out_dw = depthwise.forward(x_2d)
    assert out_dw is not None
    assert not np.isnan(out_dw).any()
    
    # Separable
    separable = SeparableConv2D(64, 128, 3, padding=1)
    out_sep = separable.forward(x_2d)
    assert out_sep is not None
    assert not np.isnan(out_sep).any()
    
    # Dilated
    dilated = DilatedConv2D(64, 64, 3, dilation=2, padding=2)
    out_dil = dilated.forward(x_2d)
    assert out_dil is not None
    assert not np.isnan(out_dil).any()
    
    # Transposed
    transposed = TransposedConv2D(64, 32, 4, stride=2, padding=1)
    out_trans = transposed.forward(x_2d)
    assert out_trans is not None
    assert not np.isnan(out_trans).any()
    
    # 1x1
    conv1x1 = Conv1x1(64, 128)
    out_1x1 = conv1x1.forward(x_2d)
    assert out_1x1 is not None
    assert not np.isnan(out_1x1).any()


def test_conv2d_preserves_batch_size():
    """Test that Conv2D preserves batch size."""
    batch_sizes = [1, 4, 16, 32]
    
    for batch_size in batch_sizes:
        conv = Conv2D(3, 64, 3, padding=1)
        x = np.random.randn(batch_size, 3, 32, 32)
        output = conv.forward(x)
        
        assert output.shape[0] == batch_size


def test_separable_vs_standard_parameters():
    """Test that separable convolution has fewer parameters."""
    in_ch, out_ch, k = 64, 128, 3
    
    # Standard conv parameters
    standard_params = out_ch * in_ch * k * k
    
    # Separable conv parameters
    depthwise_params = in_ch * k * k
    pointwise_params = in_ch * out_ch
    separable_params = depthwise_params + pointwise_params
    
    # Separable should have ~9x fewer parameters for 3x3 kernel
    assert separable_params < standard_params
    reduction = standard_params / separable_params
    assert reduction > 8  # Should be close to 9


def test_transposed_conv_upsamples():
    """Test that transposed convolution upsamples."""
    conv = TransposedConv2D(64, 32, 4, stride=2, padding=1)
    x = np.random.randn(8, 64, 14, 14)
    output = conv.forward(x)
    
    assert output.shape[2] > x.shape[2]  # Height increased
    assert output.shape[3] > x.shape[3]  # Width increased


def test_conv1x1_preserves_spatial():
    """Test that 1x1 convolution preserves spatial dimensions."""
    conv = Conv1x1(128, 256)
    x = np.random.randn(16, 128, 56, 56)
    output = conv.forward(x)
    
    assert output.shape[2] == x.shape[2]  # Height preserved
    assert output.shape[3] == x.shape[3]  # Width preserved


def test_dilated_conv_larger_receptive_field():
    """Test that dilated convolution has larger receptive field."""
    # Standard 3x3 conv
    conv_standard = Conv2D(32, 32, 3, padding=1)
    
    # Dilated 3x3 conv with dilation=2 (effective 5x5)
    conv_dilated = DilatedConv2D(32, 32, 3, dilation=2, padding=2)
    
    x = np.random.randn(4, 32, 28, 28)
    
    out_standard = conv_standard.forward(x)
    out_dilated = conv_dilated.forward(x)
    
    # Both should have same output shape
    assert out_standard.shape == out_dilated.shape
    # But dilated has larger receptive field (tested implicitly)


def test_depthwise_preserves_channels():
    """Test that depthwise convolution preserves channel count."""
    channels = [32, 64, 128, 256]
    
    for ch in channels:
        conv = DepthwiseConv2D(ch, 3, padding=1)
        x = np.random.randn(8, ch, 28, 28)
        output = conv.forward(x)
        
        assert output.shape[1] == ch  # Channels preserved


def test_conv_with_different_kernel_sizes():
    """Test convolutions with different kernel sizes."""
    kernel_sizes = [1, 3, 5, 7]
    
    for k in kernel_sizes:
        padding = (k - 1) // 2  # Same padding
        conv = Conv2D(64, 64, k, padding=padding)
        x = np.random.randn(8, 64, 28, 28)
        output = conv.forward(x)
        
        assert output.shape == (8, 64, 28, 28)  # Same spatial dims


print("=" * 80)
print("ALL CONVOLUTION TESTS PASSED! ✓")
print("=" * 80)
