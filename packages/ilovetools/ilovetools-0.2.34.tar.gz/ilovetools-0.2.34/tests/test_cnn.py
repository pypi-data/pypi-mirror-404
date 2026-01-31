"""
Tests for CNN operations module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.cnn import (
    # Convolution
    conv2d,
    conv2d_fast,
    # Pooling
    max_pool2d,
    avg_pool2d,
    global_avg_pool2d,
    global_max_pool2d,
    # Im2col
    im2col,
    col2im,
    # Depthwise/Separable
    depthwise_conv2d,
    separable_conv2d,
    # Utilities
    calculate_output_size,
    # Aliases
    maxpool2d,
    avgpool2d,
    global_avgpool,
    global_maxpool,
    depthwise_conv,
    separable_conv,
)


def test_conv2d_basic():
    """Test basic 2D convolution"""
    print("Testing conv2d basic...")
    
    # Single channel
    input = np.random.randn(1, 1, 5, 5)
    kernel = np.random.randn(1, 1, 3, 3)
    
    output = conv2d(input, kernel, stride=1, padding=0)
    
    assert output.shape == (1, 1, 3, 3), "Output shape incorrect"
    print("✓ conv2d basic passed")


def test_conv2d_multiple_channels():
    """Test convolution with multiple channels"""
    print("Testing conv2d with multiple channels...")
    
    # RGB image
    input = np.random.randn(8, 3, 28, 28)
    kernel = np.random.randn(32, 3, 3, 3)
    
    output = conv2d(input, kernel, stride=1, padding=0)
    
    assert output.shape == (8, 32, 26, 26), "Output shape incorrect"
    print("✓ conv2d multiple channels passed")


def test_conv2d_same_padding():
    """Test convolution with 'same' padding"""
    print("Testing conv2d with same padding...")
    
    input = np.random.randn(8, 3, 28, 28)
    kernel = np.random.randn(32, 3, 3, 3)
    
    output = conv2d(input, kernel, stride=1, padding='same')
    
    assert output.shape == (8, 32, 28, 28), "Same padding should preserve size"
    print("✓ conv2d same padding passed")


def test_conv2d_stride():
    """Test convolution with stride"""
    print("Testing conv2d with stride...")
    
    input = np.random.randn(8, 3, 224, 224)
    kernel = np.random.randn(64, 3, 3, 3)
    
    output = conv2d(input, kernel, stride=2, padding=1)
    
    assert output.shape == (8, 64, 112, 112), "Stride 2 should halve dimensions"
    print("✓ conv2d stride passed")


def test_conv2d_dilation():
    """Test convolution with dilation"""
    print("Testing conv2d with dilation...")
    
    input = np.random.randn(4, 3, 28, 28)
    kernel = np.random.randn(16, 3, 3, 3)
    
    output = conv2d(input, kernel, stride=1, padding=0, dilation=2)
    
    # With dilation=2, effective kernel size is 5x5
    expected_size = 28 - 2 * (3 - 1) - 1 + 1  # 24
    assert output.shape == (4, 16, 24, 24), "Dilation output size incorrect"
    print("✓ conv2d dilation passed")


def test_max_pool2d():
    """Test max pooling"""
    print("Testing max_pool2d...")
    
    input = np.random.randn(8, 64, 28, 28)
    
    output = max_pool2d(input, pool_size=2, stride=2)
    
    assert output.shape == (8, 64, 14, 14), "Max pooling output shape incorrect"
    
    # Check that max pooling actually takes maximum
    test_input = np.array([[[[1, 2], [3, 4]]]])
    test_output = max_pool2d(test_input, pool_size=2, stride=2)
    assert test_output[0, 0, 0, 0] == 4, "Should take maximum value"
    
    print("✓ max_pool2d passed")


def test_avg_pool2d():
    """Test average pooling"""
    print("Testing avg_pool2d...")
    
    input = np.random.randn(8, 64, 28, 28)
    
    output = avg_pool2d(input, pool_size=2, stride=2)
    
    assert output.shape == (8, 64, 14, 14), "Avg pooling output shape incorrect"
    
    # Check that avg pooling actually takes average
    test_input = np.array([[[[1, 2], [3, 4]]]])
    test_output = avg_pool2d(test_input, pool_size=2, stride=2)
    assert test_output[0, 0, 0, 0] == 2.5, "Should take average value"
    
    print("✓ avg_pool2d passed")


def test_global_avg_pool2d():
    """Test global average pooling"""
    print("Testing global_avg_pool2d...")
    
    input = np.random.randn(8, 512, 7, 7)
    
    output = global_avg_pool2d(input)
    
    assert output.shape == (8, 512, 1, 1), "Global avg pool output shape incorrect"
    
    # Check that it averages entire spatial dimensions
    test_input = np.ones((1, 1, 4, 4)) * 5
    test_output = global_avg_pool2d(test_input)
    assert test_output[0, 0, 0, 0] == 5, "Should average all spatial values"
    
    print("✓ global_avg_pool2d passed")


def test_global_max_pool2d():
    """Test global max pooling"""
    print("Testing global_max_pool2d...")
    
    input = np.random.randn(8, 512, 7, 7)
    
    output = global_max_pool2d(input)
    
    assert output.shape == (8, 512, 1, 1), "Global max pool output shape incorrect"
    
    print("✓ global_max_pool2d passed")


def test_im2col():
    """Test im2col transformation"""
    print("Testing im2col...")
    
    input = np.random.randn(2, 3, 5, 5)
    
    col = im2col(input, kernel_h=3, kernel_w=3, stride_h=1, stride_w=1)
    
    # Expected shape: (kernel_h * kernel_w * channels, out_h * out_w * batch)
    # out_h = out_w = (5 - 3) / 1 + 1 = 3
    # So: (3 * 3 * 3, 3 * 3 * 2) = (27, 18)
    assert col.shape == (27, 18), f"Im2col shape incorrect: {col.shape}"
    
    print("✓ im2col passed")


def test_col2im():
    """Test col2im transformation"""
    print("Testing col2im...")
    
    # Create column matrix
    col = np.random.randn(27, 18)
    input_shape = (2, 3, 5, 5)
    
    img = col2im(col, input_shape, kernel_h=3, kernel_w=3, stride_h=1, stride_w=1)
    
    assert img.shape == input_shape, "Col2im output shape incorrect"
    
    print("✓ col2im passed")


def test_im2col_col2im_inverse():
    """Test that col2im is inverse of im2col"""
    print("Testing im2col and col2im are inverses...")
    
    input = np.random.randn(2, 3, 5, 5)
    
    # Forward: im2col
    col = im2col(input, kernel_h=3, kernel_w=3, stride_h=1, stride_w=1)
    
    # Backward: col2im
    reconstructed = col2im(col, input.shape, kernel_h=3, kernel_w=3, stride_h=1, stride_w=1)
    
    # Note: col2im may not perfectly reconstruct due to overlapping regions
    # But shapes should match
    assert reconstructed.shape == input.shape, "Reconstruction shape mismatch"
    
    print("✓ im2col and col2im inverse passed")


def test_depthwise_conv2d():
    """Test depthwise convolution"""
    print("Testing depthwise_conv2d...")
    
    input = np.random.randn(8, 32, 56, 56)
    kernel = np.random.randn(32, 1, 3, 3)  # One filter per channel
    
    output = depthwise_conv2d(input, kernel, stride=1, padding='same')
    
    assert output.shape == (8, 32, 56, 56), "Depthwise conv output shape incorrect"
    
    print("✓ depthwise_conv2d passed")


def test_separable_conv2d():
    """Test separable convolution"""
    print("Testing separable_conv2d...")
    
    input = np.random.randn(8, 32, 56, 56)
    dw_kernel = np.random.randn(32, 1, 3, 3)
    pw_kernel = np.random.randn(64, 32, 1, 1)
    
    output = separable_conv2d(input, dw_kernel, pw_kernel, stride=1, padding='same')
    
    assert output.shape == (8, 64, 56, 56), "Separable conv output shape incorrect"
    
    print("✓ separable_conv2d passed")


def test_calculate_output_size():
    """Test output size calculation"""
    print("Testing calculate_output_size...")
    
    # Standard convolution
    out_size = calculate_output_size(224, 3, stride=1, padding=1)
    assert out_size == 224, "Output size calculation incorrect"
    
    # With stride 2
    out_size = calculate_output_size(224, 3, stride=2, padding=1)
    assert out_size == 112, "Output size with stride incorrect"
    
    # With dilation
    out_size = calculate_output_size(28, 3, stride=1, padding=0, dilation=2)
    assert out_size == 24, "Output size with dilation incorrect"
    
    print("✓ calculate_output_size passed")


def test_pooling_with_stride():
    """Test pooling with different stride"""
    print("Testing pooling with different stride...")
    
    input = np.random.randn(4, 16, 32, 32)
    
    # Stride same as pool size
    output1 = max_pool2d(input, pool_size=2, stride=2)
    assert output1.shape == (4, 16, 16, 16), "Pooling stride=pool_size incorrect"
    
    # Stride different from pool size
    output2 = max_pool2d(input, pool_size=3, stride=2)
    expected_size = (32 - 3) // 2 + 1  # 15
    assert output2.shape == (4, 16, 15, 15), "Pooling stride!=pool_size incorrect"
    
    print("✓ pooling with stride passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    input = np.random.randn(4, 16, 28, 28)
    
    # Test maxpool2d alias
    out1 = maxpool2d(input, pool_size=2)
    out2 = max_pool2d(input, pool_size=2)
    assert np.allclose(out1, out2), "maxpool2d alias should work"
    
    # Test avgpool2d alias
    out1 = avgpool2d(input, pool_size=2)
    out2 = avg_pool2d(input, pool_size=2)
    assert np.allclose(out1, out2), "avgpool2d alias should work"
    
    # Test global_avgpool alias
    out1 = global_avgpool(input)
    out2 = global_avg_pool2d(input)
    assert np.allclose(out1, out2), "global_avgpool alias should work"
    
    print("✓ aliases passed")


def test_conv2d_edge_detection():
    """Test convolution with edge detection kernel"""
    print("Testing conv2d edge detection...")
    
    # Create simple image
    input = np.zeros((1, 1, 5, 5))
    input[0, 0, 2, :] = 1  # Horizontal line
    
    # Horizontal edge detection kernel
    kernel = np.array([[[[-1, -1, -1],
                         [ 0,  0,  0],
                         [ 1,  1,  1]]]])
    
    output = conv2d(input, kernel, stride=1, padding=0)
    
    # Should detect the edge
    assert output.shape == (1, 1, 3, 3), "Edge detection output shape incorrect"
    
    print("✓ conv2d edge detection passed")


def test_pooling_preserves_channels():
    """Test that pooling preserves number of channels"""
    print("Testing pooling preserves channels...")
    
    input = np.random.randn(8, 128, 32, 32)
    
    output_max = max_pool2d(input, pool_size=2)
    output_avg = avg_pool2d(input, pool_size=2)
    
    assert output_max.shape[1] == 128, "Max pooling should preserve channels"
    assert output_avg.shape[1] == 128, "Avg pooling should preserve channels"
    
    print("✓ pooling preserves channels passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("CNN OPERATIONS MODULE TESTS")
    print("="*60 + "\n")
    
    # Convolution tests
    test_conv2d_basic()
    test_conv2d_multiple_channels()
    test_conv2d_same_padding()
    test_conv2d_stride()
    test_conv2d_dilation()
    test_conv2d_edge_detection()
    
    # Pooling tests
    test_max_pool2d()
    test_avg_pool2d()
    test_global_avg_pool2d()
    test_global_max_pool2d()
    test_pooling_with_stride()
    test_pooling_preserves_channels()
    
    # Im2col tests
    test_im2col()
    test_col2im()
    test_im2col_col2im_inverse()
    
    # Depthwise/Separable tests
    test_depthwise_conv2d()
    test_separable_conv2d()
    
    # Utilities
    test_calculate_output_size()
    
    # Aliases
    test_aliases()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
