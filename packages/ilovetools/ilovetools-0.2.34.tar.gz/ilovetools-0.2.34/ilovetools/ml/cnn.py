"""
Convolutional Neural Network Operations

This module provides core CNN operations:
- 2D Convolution (Conv2D)
- Pooling Operations (Max, Average, Global)
- Padding Strategies (Same, Valid, Custom)
- Im2Col and Col2Im transformations
- Depthwise and Separable Convolutions
- Dilated Convolutions

All operations support batched inputs and are optimized for performance.
"""

import numpy as np
from typing import Tuple, Union, Optional


# ============================================================================
# 2D CONVOLUTION
# ============================================================================

def conv2d(
    input: np.ndarray,
    kernel: np.ndarray,
    stride: Union[int, Tuple[int, int]] = 1,
    padding: Union[str, int, Tuple[int, int]] = 0,
    dilation: Union[int, Tuple[int, int]] = 1
) -> np.ndarray:
    """
    2D Convolution Operation
    
    Applies a 2D convolution over an input signal composed of several input planes.
    
    Args:
        input: Input tensor of shape (batch, in_channels, height, width)
        kernel: Kernel tensor of shape (out_channels, in_channels, kernel_h, kernel_w)
        stride: Stride of the convolution (default: 1)
        padding: Padding added to input ('same', 'valid', or int/tuple)
        dilation: Spacing between kernel elements (default: 1)
        
    Returns:
        Output tensor of shape (batch, out_channels, out_height, out_width)
        
    Example:
        >>> # Single channel convolution
        >>> input = np.random.randn(1, 1, 28, 28)  # (batch, channels, H, W)
        >>> kernel = np.random.randn(32, 1, 3, 3)  # (out_ch, in_ch, kH, kW)
        >>> output = conv2d(input, kernel, stride=1, padding='same')
        >>> print(output.shape)  # (1, 32, 28, 28)
        
        >>> # RGB image convolution
        >>> input = np.random.randn(8, 3, 224, 224)  # RGB images
        >>> kernel = np.random.randn(64, 3, 3, 3)  # 64 filters
        >>> output = conv2d(input, kernel, stride=2, padding=1)
        >>> print(output.shape)  # (8, 64, 112, 112)
    """
    # Parse stride
    if isinstance(stride, int):
        stride_h, stride_w = stride, stride
    else:
        stride_h, stride_w = stride
    
    # Parse dilation
    if isinstance(dilation, int):
        dilation_h, dilation_w = dilation, dilation
    else:
        dilation_h, dilation_w = dilation
    
    # Get dimensions
    batch_size, in_channels, in_h, in_w = input.shape
    out_channels, _, kernel_h, kernel_w = kernel.shape
    
    # Apply padding
    if isinstance(padding, str):
        if padding == 'same':
            # Calculate padding for 'same' output size
            pad_h = ((in_h - 1) * stride_h + dilation_h * (kernel_h - 1) + 1 - in_h) // 2
            pad_w = ((in_w - 1) * stride_w + dilation_w * (kernel_w - 1) + 1 - in_w) // 2
            pad_h, pad_w = max(0, pad_h), max(0, pad_w)
        elif padding == 'valid':
            pad_h, pad_w = 0, 0
        else:
            raise ValueError(f"Unknown padding mode: {padding}")
    elif isinstance(padding, int):
        pad_h, pad_w = padding, padding
    else:
        pad_h, pad_w = padding
    
    # Pad input
    if pad_h > 0 or pad_w > 0:
        input = np.pad(input, ((0, 0), (0, 0), (pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        in_h, in_w = input.shape[2], input.shape[3]
    
    # Calculate output dimensions
    out_h = (in_h - dilation_h * (kernel_h - 1) - 1) // stride_h + 1
    out_w = (in_w - dilation_w * (kernel_w - 1) - 1) // stride_w + 1
    
    # Initialize output
    output = np.zeros((batch_size, out_channels, out_h, out_w))
    
    # Perform convolution
    for b in range(batch_size):
        for oc in range(out_channels):
            for i in range(out_h):
                for j in range(out_w):
                    # Calculate input region
                    h_start = i * stride_h
                    w_start = j * stride_w
                    
                    # Extract region with dilation
                    region = input[b, :, 
                                  h_start:h_start + dilation_h * kernel_h:dilation_h,
                                  w_start:w_start + dilation_w * kernel_w:dilation_w]
                    
                    # Convolve
                    output[b, oc, i, j] = np.sum(region * kernel[oc])
    
    return output


def conv2d_fast(
    input: np.ndarray,
    kernel: np.ndarray,
    stride: Union[int, Tuple[int, int]] = 1,
    padding: Union[str, int, Tuple[int, int]] = 0
) -> np.ndarray:
    """
    Fast 2D Convolution using im2col
    
    More efficient implementation using matrix multiplication.
    
    Args:
        input: Input tensor of shape (batch, in_channels, height, width)
        kernel: Kernel tensor of shape (out_channels, in_channels, kernel_h, kernel_w)
        stride: Stride of the convolution
        padding: Padding added to input
        
    Returns:
        Output tensor of shape (batch, out_channels, out_height, out_width)
        
    Example:
        >>> input = np.random.randn(8, 3, 224, 224)
        >>> kernel = np.random.randn(64, 3, 3, 3)
        >>> output = conv2d_fast(input, kernel, stride=1, padding='same')
        >>> print(output.shape)  # (8, 64, 224, 224)
    """
    # Parse stride
    if isinstance(stride, int):
        stride_h, stride_w = stride, stride
    else:
        stride_h, stride_w = stride
    
    # Get dimensions
    batch_size, in_channels, in_h, in_w = input.shape
    out_channels, _, kernel_h, kernel_w = kernel.shape
    
    # Apply padding
    if isinstance(padding, str):
        if padding == 'same':
            pad_h = ((in_h - 1) * stride_h + kernel_h - in_h) // 2
            pad_w = ((in_w - 1) * stride_w + kernel_w - in_w) // 2
            pad_h, pad_w = max(0, pad_h), max(0, pad_w)
        elif padding == 'valid':
            pad_h, pad_w = 0, 0
    elif isinstance(padding, int):
        pad_h, pad_w = padding, padding
    else:
        pad_h, pad_w = padding
    
    # Pad input
    if pad_h > 0 or pad_w > 0:
        input = np.pad(input, ((0, 0), (0, 0), (pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        in_h, in_w = input.shape[2], input.shape[3]
    
    # Calculate output dimensions
    out_h = (in_h - kernel_h) // stride_h + 1
    out_w = (in_w - kernel_w) // stride_w + 1
    
    # Im2col transformation
    col = im2col(input, kernel_h, kernel_w, stride_h, stride_w)
    
    # Reshape kernel
    kernel_col = kernel.reshape(out_channels, -1)
    
    # Matrix multiplication
    output = np.dot(kernel_col, col)
    
    # Reshape output
    output = output.reshape(out_channels, out_h, out_w, batch_size)
    output = output.transpose(3, 0, 1, 2)
    
    return output


# ============================================================================
# POOLING OPERATIONS
# ============================================================================

def max_pool2d(
    input: np.ndarray,
    pool_size: Union[int, Tuple[int, int]] = 2,
    stride: Optional[Union[int, Tuple[int, int]]] = None,
    padding: Union[int, Tuple[int, int]] = 0
) -> np.ndarray:
    """
    2D Max Pooling
    
    Applies a 2D max pooling over an input signal.
    
    Args:
        input: Input tensor of shape (batch, channels, height, width)
        pool_size: Size of the pooling window (default: 2)
        stride: Stride of the pooling (default: same as pool_size)
        padding: Padding added to input (default: 0)
        
    Returns:
        Output tensor after max pooling
        
    Example:
        >>> input = np.random.randn(8, 64, 28, 28)
        >>> output = max_pool2d(input, pool_size=2, stride=2)
        >>> print(output.shape)  # (8, 64, 14, 14)
    """
    # Parse pool_size
    if isinstance(pool_size, int):
        pool_h, pool_w = pool_size, pool_size
    else:
        pool_h, pool_w = pool_size
    
    # Parse stride (default to pool_size)
    if stride is None:
        stride_h, stride_w = pool_h, pool_w
    elif isinstance(stride, int):
        stride_h, stride_w = stride, stride
    else:
        stride_h, stride_w = stride
    
    # Parse padding
    if isinstance(padding, int):
        pad_h, pad_w = padding, padding
    else:
        pad_h, pad_w = padding
    
    # Get dimensions
    batch_size, channels, in_h, in_w = input.shape
    
    # Apply padding
    if pad_h > 0 or pad_w > 0:
        input = np.pad(input, ((0, 0), (0, 0), (pad_h, pad_h), (pad_w, pad_w)), 
                      mode='constant', constant_values=-np.inf)
        in_h, in_w = input.shape[2], input.shape[3]
    
    # Calculate output dimensions
    out_h = (in_h - pool_h) // stride_h + 1
    out_w = (in_w - pool_w) // stride_w + 1
    
    # Initialize output
    output = np.zeros((batch_size, channels, out_h, out_w))
    
    # Perform max pooling
    for b in range(batch_size):
        for c in range(channels):
            for i in range(out_h):
                for j in range(out_w):
                    h_start = i * stride_h
                    w_start = j * stride_w
                    
                    # Extract region
                    region = input[b, c, h_start:h_start + pool_h, w_start:w_start + pool_w]
                    
                    # Take maximum
                    output[b, c, i, j] = np.max(region)
    
    return output


def avg_pool2d(
    input: np.ndarray,
    pool_size: Union[int, Tuple[int, int]] = 2,
    stride: Optional[Union[int, Tuple[int, int]]] = None,
    padding: Union[int, Tuple[int, int]] = 0
) -> np.ndarray:
    """
    2D Average Pooling
    
    Applies a 2D average pooling over an input signal.
    
    Args:
        input: Input tensor of shape (batch, channels, height, width)
        pool_size: Size of the pooling window (default: 2)
        stride: Stride of the pooling (default: same as pool_size)
        padding: Padding added to input (default: 0)
        
    Returns:
        Output tensor after average pooling
        
    Example:
        >>> input = np.random.randn(8, 64, 28, 28)
        >>> output = avg_pool2d(input, pool_size=2, stride=2)
        >>> print(output.shape)  # (8, 64, 14, 14)
    """
    # Parse pool_size
    if isinstance(pool_size, int):
        pool_h, pool_w = pool_size, pool_size
    else:
        pool_h, pool_w = pool_size
    
    # Parse stride
    if stride is None:
        stride_h, stride_w = pool_h, pool_w
    elif isinstance(stride, int):
        stride_h, stride_w = stride, stride
    else:
        stride_h, stride_w = stride
    
    # Parse padding
    if isinstance(padding, int):
        pad_h, pad_w = padding, padding
    else:
        pad_h, pad_w = padding
    
    # Get dimensions
    batch_size, channels, in_h, in_w = input.shape
    
    # Apply padding
    if pad_h > 0 or pad_w > 0:
        input = np.pad(input, ((0, 0), (0, 0), (pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        in_h, in_w = input.shape[2], input.shape[3]
    
    # Calculate output dimensions
    out_h = (in_h - pool_h) // stride_h + 1
    out_w = (in_w - pool_w) // stride_w + 1
    
    # Initialize output
    output = np.zeros((batch_size, channels, out_h, out_w))
    
    # Perform average pooling
    for b in range(batch_size):
        for c in range(channels):
            for i in range(out_h):
                for j in range(out_w):
                    h_start = i * stride_h
                    w_start = j * stride_w
                    
                    # Extract region
                    region = input[b, c, h_start:h_start + pool_h, w_start:w_start + pool_w]
                    
                    # Take average
                    output[b, c, i, j] = np.mean(region)
    
    return output


def global_avg_pool2d(input: np.ndarray) -> np.ndarray:
    """
    Global Average Pooling
    
    Averages each feature map to a single value.
    
    Args:
        input: Input tensor of shape (batch, channels, height, width)
        
    Returns:
        Output tensor of shape (batch, channels, 1, 1)
        
    Example:
        >>> input = np.random.randn(8, 512, 7, 7)
        >>> output = global_avg_pool2d(input)
        >>> print(output.shape)  # (8, 512, 1, 1)
    """
    return np.mean(input, axis=(2, 3), keepdims=True)


def global_max_pool2d(input: np.ndarray) -> np.ndarray:
    """
    Global Max Pooling
    
    Takes maximum of each feature map.
    
    Args:
        input: Input tensor of shape (batch, channels, height, width)
        
    Returns:
        Output tensor of shape (batch, channels, 1, 1)
        
    Example:
        >>> input = np.random.randn(8, 512, 7, 7)
        >>> output = global_max_pool2d(input)
        >>> print(output.shape)  # (8, 512, 1, 1)
    """
    return np.max(input, axis=(2, 3), keepdims=True)


# ============================================================================
# IM2COL TRANSFORMATION
# ============================================================================

def im2col(
    input: np.ndarray,
    kernel_h: int,
    kernel_w: int,
    stride_h: int = 1,
    stride_w: int = 1
) -> np.ndarray:
    """
    Im2Col transformation for efficient convolution
    
    Transforms image into column matrix for matrix multiplication.
    
    Args:
        input: Input tensor of shape (batch, channels, height, width)
        kernel_h: Kernel height
        kernel_w: Kernel width
        stride_h: Vertical stride
        stride_w: Horizontal stride
        
    Returns:
        Column matrix of shape (kernel_h * kernel_w * channels, out_h * out_w * batch)
        
    Example:
        >>> input = np.random.randn(8, 3, 32, 32)
        >>> col = im2col(input, kernel_h=3, kernel_w=3, stride_h=1, stride_w=1)
        >>> print(col.shape)  # (27, 7200)
    """
    batch_size, channels, in_h, in_w = input.shape
    
    # Calculate output dimensions
    out_h = (in_h - kernel_h) // stride_h + 1
    out_w = (in_w - kernel_w) // stride_w + 1
    
    # Initialize column matrix
    col = np.zeros((batch_size, channels, kernel_h, kernel_w, out_h, out_w))
    
    # Fill column matrix
    for i in range(kernel_h):
        i_max = i + stride_h * out_h
        for j in range(kernel_w):
            j_max = j + stride_w * out_w
            col[:, :, i, j, :, :] = input[:, :, i:i_max:stride_h, j:j_max:stride_w]
    
    # Reshape
    col = col.transpose(0, 4, 5, 1, 2, 3).reshape(batch_size * out_h * out_w, -1)
    
    return col.T


def col2im(
    col: np.ndarray,
    input_shape: Tuple[int, int, int, int],
    kernel_h: int,
    kernel_w: int,
    stride_h: int = 1,
    stride_w: int = 1
) -> np.ndarray:
    """
    Col2Im transformation (inverse of im2col)
    
    Transforms column matrix back to image format.
    
    Args:
        col: Column matrix
        input_shape: Original input shape (batch, channels, height, width)
        kernel_h: Kernel height
        kernel_w: Kernel width
        stride_h: Vertical stride
        stride_w: Horizontal stride
        
    Returns:
        Image tensor of shape input_shape
        
    Example:
        >>> col = np.random.randn(27, 7200)
        >>> img = col2im(col, (8, 3, 32, 32), kernel_h=3, kernel_w=3)
        >>> print(img.shape)  # (8, 3, 32, 32)
    """
    batch_size, channels, in_h, in_w = input_shape
    
    # Calculate output dimensions
    out_h = (in_h - kernel_h) // stride_h + 1
    out_w = (in_w - kernel_w) // stride_w + 1
    
    # Reshape column
    col = col.T.reshape(batch_size, out_h, out_w, channels, kernel_h, kernel_w)
    col = col.transpose(0, 3, 4, 5, 1, 2)
    
    # Initialize image
    img = np.zeros(input_shape)
    
    # Fill image
    for i in range(kernel_h):
        i_max = i + stride_h * out_h
        for j in range(kernel_w):
            j_max = j + stride_w * out_w
            img[:, :, i:i_max:stride_h, j:j_max:stride_w] += col[:, :, i, j, :, :]
    
    return img


# ============================================================================
# DEPTHWISE AND SEPARABLE CONVOLUTIONS
# ============================================================================

def depthwise_conv2d(
    input: np.ndarray,
    kernel: np.ndarray,
    stride: Union[int, Tuple[int, int]] = 1,
    padding: Union[str, int, Tuple[int, int]] = 0
) -> np.ndarray:
    """
    Depthwise 2D Convolution
    
    Applies a separate filter to each input channel.
    Used in MobileNets for efficiency.
    
    Args:
        input: Input tensor of shape (batch, in_channels, height, width)
        kernel: Kernel tensor of shape (in_channels, 1, kernel_h, kernel_w)
        stride: Stride of the convolution
        padding: Padding added to input
        
    Returns:
        Output tensor of shape (batch, in_channels, out_height, out_width)
        
    Example:
        >>> input = np.random.randn(8, 32, 56, 56)
        >>> kernel = np.random.randn(32, 1, 3, 3)  # One filter per channel
        >>> output = depthwise_conv2d(input, kernel, stride=1, padding='same')
        >>> print(output.shape)  # (8, 32, 56, 56)
    """
    batch_size, in_channels, _, _ = input.shape
    
    # Apply convolution to each channel separately
    outputs = []
    for c in range(in_channels):
        channel_input = input[:, c:c+1, :, :]
        channel_kernel = kernel[c:c+1, :, :, :]
        channel_output = conv2d(channel_input, channel_kernel, stride, padding)
        outputs.append(channel_output)
    
    return np.concatenate(outputs, axis=1)


def separable_conv2d(
    input: np.ndarray,
    depthwise_kernel: np.ndarray,
    pointwise_kernel: np.ndarray,
    stride: Union[int, Tuple[int, int]] = 1,
    padding: Union[str, int, Tuple[int, int]] = 0
) -> np.ndarray:
    """
    Separable 2D Convolution (Depthwise + Pointwise)
    
    Efficient convolution used in MobileNets.
    
    Args:
        input: Input tensor of shape (batch, in_channels, height, width)
        depthwise_kernel: Depthwise kernel (in_channels, 1, kernel_h, kernel_w)
        pointwise_kernel: Pointwise kernel (out_channels, in_channels, 1, 1)
        stride: Stride of the depthwise convolution
        padding: Padding for depthwise convolution
        
    Returns:
        Output tensor of shape (batch, out_channels, out_height, out_width)
        
    Example:
        >>> input = np.random.randn(8, 32, 56, 56)
        >>> dw_kernel = np.random.randn(32, 1, 3, 3)
        >>> pw_kernel = np.random.randn(64, 32, 1, 1)
        >>> output = separable_conv2d(input, dw_kernel, pw_kernel)
        >>> print(output.shape)  # (8, 64, 56, 56)
    """
    # Depthwise convolution
    depthwise_output = depthwise_conv2d(input, depthwise_kernel, stride, padding)
    
    # Pointwise convolution (1x1)
    pointwise_output = conv2d(depthwise_output, pointwise_kernel, stride=1, padding=0)
    
    return pointwise_output


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_output_size(
    input_size: int,
    kernel_size: int,
    stride: int = 1,
    padding: int = 0,
    dilation: int = 1
) -> int:
    """
    Calculate output size after convolution or pooling
    
    Args:
        input_size: Input dimension size
        kernel_size: Kernel dimension size
        stride: Stride
        padding: Padding
        dilation: Dilation
        
    Returns:
        Output dimension size
        
    Example:
        >>> out_size = calculate_output_size(224, 3, stride=2, padding=1)
        >>> print(out_size)  # 112
    """
    return (input_size + 2 * padding - dilation * (kernel_size - 1) - 1) // stride + 1


# Aliases for convenience
maxpool2d = max_pool2d
avgpool2d = avg_pool2d
global_avgpool = global_avg_pool2d
global_maxpool = global_max_pool2d
depthwise_conv = depthwise_conv2d
separable_conv = separable_conv2d
