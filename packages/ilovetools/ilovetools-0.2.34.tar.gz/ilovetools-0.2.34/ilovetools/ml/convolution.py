"""
Convolution Operations Suite

This module implements various convolution operations for neural networks.
Convolutions are the foundation of CNNs, extracting spatial features from data.

Implemented Convolution Types:
1. Conv1D - 1D convolution for sequences (text, audio, time series)
2. Conv2D - 2D convolution for images (standard CNN layer)
3. Conv3D - 3D convolution for videos, volumetric data
4. DepthwiseConv2D - Depthwise convolution (spatial filtering per channel)
5. SeparableConv2D - Depthwise separable convolution (efficient)
6. DilatedConv2D - Dilated/Atrous convolution (expanded receptive field)
7. TransposedConv2D - Transposed convolution (upsampling)
8. Conv1x1 - 1x1 convolution (channel mixing, dimensionality reduction)

References:
- Standard Convolution: LeCun et al., "Gradient-Based Learning Applied to Document Recognition" (1998)
- Depthwise Separable: Chollet, "Xception: Deep Learning with Depthwise Separable Convolutions" (2017)
- Dilated Convolution: Yu & Koltun, "Multi-Scale Context Aggregation by Dilated Convolutions" (2016)
- Transposed Convolution: Zeiler et al., "Deconvolutional Networks" (2010)

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
from typing import Union, Tuple, Optional


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_conv_output_size(input_size: int, kernel_size: int, stride: int, 
                          padding: int, dilation: int = 1) -> int:
    """Calculate output size for convolution."""
    effective_kernel = dilation * (kernel_size - 1) + 1
    return (input_size + 2 * padding - effective_kernel) // stride + 1


def _pad_input(x: np.ndarray, padding: Union[int, Tuple[int, int]], 
               mode: str = 'constant') -> np.ndarray:
    """Add padding to input."""
    if isinstance(padding, int):
        pad_h = pad_w = padding
    else:
        pad_h, pad_w = padding
    
    if x.ndim == 3:  # (batch, channels, length)
        return np.pad(x, ((0, 0), (0, 0), (pad_w, pad_w)), mode=mode)
    elif x.ndim == 4:  # (batch, channels, height, width)
        return np.pad(x, ((0, 0), (0, 0), (pad_h, pad_h), (pad_w, pad_w)), mode=mode)
    else:
        raise ValueError(f"Unsupported input dimensions: {x.ndim}")


# ============================================================================
# CONV1D
# ============================================================================

class Conv1D:
    """
    1D Convolution Layer.
    
    Applies 1D convolution over sequences (text, audio, time series).
    
    Formula:
        output[b, f, i] = Σ(input[b, c, i*stride + k] * kernel[f, c, k]) + bias[f]
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels (filters)
        kernel_size: Size of convolution kernel
        stride: Stride of convolution (default: 1)
        padding: Padding to add (default: 0)
        dilation: Dilation rate (default: 1)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = Conv1D(in_channels=128, out_channels=256, kernel_size=3)
        >>> x = np.random.randn(32, 128, 100)  # (batch, channels, length)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 256, 98)
    
    Use Case:
        Text classification, audio processing, time series analysis
    
    Reference:
        Standard practice in sequence modeling
    """
    
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int,
                 stride: int = 1, padding: int = 0, dilation: int = 1, bias: bool = True):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.use_bias = bias
        
        # Initialize weights (He initialization)
        self.weight = np.random.randn(out_channels, in_channels, kernel_size) * np.sqrt(2.0 / in_channels)
        self.bias = np.zeros(out_channels) if bias else None
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, in_channels, length)
        
        Returns:
            Output tensor (batch, out_channels, out_length)
        """
        batch_size, in_channels, length = x.shape
        
        if in_channels != self.in_channels:
            raise ValueError(f"Expected {self.in_channels} input channels, got {in_channels}")
        
        # Apply padding
        if self.padding > 0:
            x_padded = _pad_input(x, self.padding)
        else:
            x_padded = x
        
        # Calculate output length
        out_length = _get_conv_output_size(x_padded.shape[2], self.kernel_size, 
                                          self.stride, 0, self.dilation)
        
        # Initialize output
        output = np.zeros((batch_size, self.out_channels, out_length))
        
        # Perform convolution
        for b in range(batch_size):
            for f in range(self.out_channels):
                for i in range(out_length):
                    start = i * self.stride
                    
                    # Extract window with dilation
                    window_sum = 0
                    for c in range(self.in_channels):
                        for k in range(self.kernel_size):
                            pos = start + k * self.dilation
                            if pos < x_padded.shape[2]:
                                window_sum += x_padded[b, c, pos] * self.weight[f, c, k]
                    
                    output[b, f, i] = window_sum
                    if self.use_bias:
                        output[b, f, i] += self.bias[f]
        
        self.cache = x
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# CONV2D
# ============================================================================

class Conv2D:
    """
    2D Convolution Layer.
    
    Standard convolution for images. Foundation of CNNs.
    
    Formula:
        output[b,f,i,j] = Σ(input[b,c,i*s+m,j*s+n] * kernel[f,c,m,n]) + bias[f]
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels (filters)
        kernel_size: Size of convolution kernel (int or tuple)
        stride: Stride of convolution (default: 1)
        padding: Padding to add (default: 0, or 'same', 'valid')
        dilation: Dilation rate (default: 1)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = Conv2D(in_channels=3, out_channels=64, kernel_size=3, padding='same')
        >>> x = np.random.randn(32, 3, 224, 224)  # (batch, channels, height, width)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 64, 224, 224)
    
    Use Case:
        Image classification, object detection, segmentation
    
    Reference:
        LeCun et al., "Gradient-Based Learning Applied to Document Recognition" (1998)
    """
    
    def __init__(self, in_channels: int, out_channels: int, 
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[int, Tuple[int, int], str] = 0,
                 dilation: Union[int, Tuple[int, int]] = 1,
                 bias: bool = True):
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # Handle kernel_size
        if isinstance(kernel_size, int):
            self.kernel_h, self.kernel_w = kernel_size, kernel_size
        else:
            self.kernel_h, self.kernel_w = kernel_size
        
        # Handle stride
        if isinstance(stride, int):
            self.stride_h, self.stride_w = stride, stride
        else:
            self.stride_h, self.stride_w = stride
        
        # Handle padding
        if isinstance(padding, str):
            if padding == 'same':
                self.pad_h = (self.kernel_h - 1) // 2
                self.pad_w = (self.kernel_w - 1) // 2
            elif padding == 'valid':
                self.pad_h = self.pad_w = 0
            else:
                raise ValueError(f"Unknown padding mode: {padding}")
        elif isinstance(padding, int):
            self.pad_h = self.pad_w = padding
        else:
            self.pad_h, self.pad_w = padding
        
        # Handle dilation
        if isinstance(dilation, int):
            self.dilation_h, self.dilation_w = dilation, dilation
        else:
            self.dilation_h, self.dilation_w = dilation
        
        self.use_bias = bias
        
        # Initialize weights (He initialization)
        self.weight = np.random.randn(out_channels, in_channels, self.kernel_h, self.kernel_w) * \
                     np.sqrt(2.0 / (in_channels * self.kernel_h * self.kernel_w))
        self.bias = np.zeros(out_channels) if bias else None
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, in_channels, height, width)
        
        Returns:
            Output tensor (batch, out_channels, out_height, out_width)
        """
        batch_size, in_channels, height, width = x.shape
        
        if in_channels != self.in_channels:
            raise ValueError(f"Expected {self.in_channels} input channels, got {in_channels}")
        
        # Apply padding
        if self.pad_h > 0 or self.pad_w > 0:
            x_padded = _pad_input(x, (self.pad_h, self.pad_w))
        else:
            x_padded = x
        
        # Calculate output dimensions
        out_h = _get_conv_output_size(x_padded.shape[2], self.kernel_h, 
                                      self.stride_h, 0, self.dilation_h)
        out_w = _get_conv_output_size(x_padded.shape[3], self.kernel_w, 
                                      self.stride_w, 0, self.dilation_w)
        
        # Initialize output
        output = np.zeros((batch_size, self.out_channels, out_h, out_w))
        
        # Perform convolution
        for b in range(batch_size):
            for f in range(self.out_channels):
                for i in range(out_h):
                    for j in range(out_w):
                        h_start = i * self.stride_h
                        w_start = j * self.stride_w
                        
                        # Extract window with dilation
                        window_sum = 0
                        for c in range(self.in_channels):
                            for m in range(self.kernel_h):
                                for n in range(self.kernel_w):
                                    h_pos = h_start + m * self.dilation_h
                                    w_pos = w_start + n * self.dilation_w
                                    
                                    if h_pos < x_padded.shape[2] and w_pos < x_padded.shape[3]:
                                        window_sum += x_padded[b, c, h_pos, w_pos] * \
                                                    self.weight[f, c, m, n]
                        
                        output[b, f, i, j] = window_sum
                        if self.use_bias:
                            output[b, f, i, j] += self.bias[f]
        
        self.cache = x
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# CONV3D
# ============================================================================

class Conv3D:
    """
    3D Convolution Layer.
    
    Applies 3D convolution over volumetric data (videos, medical imaging).
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels (filters)
        kernel_size: Size of convolution kernel (int or tuple)
        stride: Stride of convolution (default: 1)
        padding: Padding to add (default: 0)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = Conv3D(in_channels=3, out_channels=64, kernel_size=3)
        >>> x = np.random.randn(8, 3, 16, 112, 112)  # (batch, channels, depth, height, width)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (8, 64, 14, 110, 110)
    
    Use Case:
        Video classification, action recognition, 3D medical imaging
    
    Reference:
        Ji et al., "3D Convolutional Neural Networks for Human Action Recognition" (2013)
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: Union[int, Tuple[int, int, int]],
                 stride: Union[int, Tuple[int, int, int]] = 1,
                 padding: Union[int, Tuple[int, int, int]] = 0,
                 bias: bool = True):
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # Handle kernel_size
        if isinstance(kernel_size, int):
            self.kernel_d, self.kernel_h, self.kernel_w = kernel_size, kernel_size, kernel_size
        else:
            self.kernel_d, self.kernel_h, self.kernel_w = kernel_size
        
        # Handle stride
        if isinstance(stride, int):
            self.stride_d, self.stride_h, self.stride_w = stride, stride, stride
        else:
            self.stride_d, self.stride_h, self.stride_w = stride
        
        # Handle padding
        if isinstance(padding, int):
            self.pad_d, self.pad_h, self.pad_w = padding, padding, padding
        else:
            self.pad_d, self.pad_h, self.pad_w = padding
        
        self.use_bias = bias
        
        # Initialize weights
        self.weight = np.random.randn(out_channels, in_channels, 
                                     self.kernel_d, self.kernel_h, self.kernel_w) * \
                     np.sqrt(2.0 / (in_channels * self.kernel_d * self.kernel_h * self.kernel_w))
        self.bias = np.zeros(out_channels) if bias else None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, in_channels, depth, height, width)
        
        Returns:
            Output tensor (batch, out_channels, out_depth, out_height, out_width)
        """
        batch_size, in_channels, depth, height, width = x.shape
        
        # Apply padding
        if self.pad_d > 0 or self.pad_h > 0 or self.pad_w > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), 
                                 (self.pad_d, self.pad_d),
                                 (self.pad_h, self.pad_h),
                                 (self.pad_w, self.pad_w)), mode='constant')
        else:
            x_padded = x
        
        # Calculate output dimensions
        out_d = (x_padded.shape[2] - self.kernel_d) // self.stride_d + 1
        out_h = (x_padded.shape[3] - self.kernel_h) // self.stride_h + 1
        out_w = (x_padded.shape[4] - self.kernel_w) // self.stride_w + 1
        
        # Initialize output
        output = np.zeros((batch_size, self.out_channels, out_d, out_h, out_w))
        
        # Perform 3D convolution (simplified for demonstration)
        for b in range(batch_size):
            for f in range(self.out_channels):
                for d in range(out_d):
                    for i in range(out_h):
                        for j in range(out_w):
                            d_start = d * self.stride_d
                            h_start = i * self.stride_h
                            w_start = j * self.stride_w
                            
                            window = x_padded[b, :, 
                                            d_start:d_start+self.kernel_d,
                                            h_start:h_start+self.kernel_h,
                                            w_start:w_start+self.kernel_w]
                            
                            output[b, f, d, i, j] = np.sum(window * self.weight[f])
                            if self.use_bias:
                                output[b, f, d, i, j] += self.bias[f]
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# DEPTHWISE CONV2D
# ============================================================================

class DepthwiseConv2D:
    """
    Depthwise 2D Convolution.
    
    Applies spatial convolution independently to each input channel.
    First step of depthwise separable convolution.
    
    Formula:
        output[b,c,i,j] = Σ(input[b,c,i*s+m,j*s+n] * kernel[c,m,n]) + bias[c]
    
    Args:
        in_channels: Number of input channels
        kernel_size: Size of convolution kernel
        stride: Stride of convolution (default: 1)
        padding: Padding to add (default: 0)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = DepthwiseConv2D(in_channels=64, kernel_size=3, padding=1)
        >>> x = np.random.randn(32, 64, 56, 56)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 64, 56, 56)
    
    Use Case:
        MobileNet, EfficientNet (efficient mobile architectures)
    
    Reference:
        Chollet, "Xception: Deep Learning with Depthwise Separable Convolutions" (2017)
    """
    
    def __init__(self, in_channels: int, kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[int, Tuple[int, int]] = 0,
                 bias: bool = True):
        self.in_channels = in_channels
        
        if isinstance(kernel_size, int):
            self.kernel_h, self.kernel_w = kernel_size, kernel_size
        else:
            self.kernel_h, self.kernel_w = kernel_size
        
        if isinstance(stride, int):
            self.stride_h, self.stride_w = stride, stride
        else:
            self.stride_h, self.stride_w = stride
        
        if isinstance(padding, int):
            self.pad_h = self.pad_w = padding
        else:
            self.pad_h, self.pad_w = padding
        
        self.use_bias = bias
        
        # One kernel per input channel
        self.weight = np.random.randn(in_channels, self.kernel_h, self.kernel_w) * \
                     np.sqrt(2.0 / (self.kernel_h * self.kernel_w))
        self.bias = np.zeros(in_channels) if bias else None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, in_channels, height, width = x.shape
        
        # Apply padding
        if self.pad_h > 0 or self.pad_w > 0:
            x_padded = _pad_input(x, (self.pad_h, self.pad_w))
        else:
            x_padded = x
        
        # Calculate output dimensions
        out_h = (x_padded.shape[2] - self.kernel_h) // self.stride_h + 1
        out_w = (x_padded.shape[3] - self.kernel_w) // self.stride_w + 1
        
        # Initialize output
        output = np.zeros((batch_size, in_channels, out_h, out_w))
        
        # Depthwise convolution (one filter per channel)
        for b in range(batch_size):
            for c in range(in_channels):
                for i in range(out_h):
                    for j in range(out_w):
                        h_start = i * self.stride_h
                        w_start = j * self.stride_w
                        
                        window = x_padded[b, c, 
                                        h_start:h_start+self.kernel_h,
                                        w_start:w_start+self.kernel_w]
                        
                        output[b, c, i, j] = np.sum(window * self.weight[c])
                        if self.use_bias:
                            output[b, c, i, j] += self.bias[c]
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# SEPARABLE CONV2D
# ============================================================================

class SeparableConv2D:
    """
    Depthwise Separable 2D Convolution.
    
    Combines depthwise convolution + pointwise (1x1) convolution.
    Dramatically reduces parameters and computation.
    
    Parameters:
        Standard Conv: in_ch * out_ch * k * k
        Separable Conv: in_ch * k * k + in_ch * out_ch
        Reduction: ~9x for 3x3 kernels
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        kernel_size: Size of depthwise kernel
        stride: Stride of depthwise convolution (default: 1)
        padding: Padding for depthwise convolution (default: 0)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = SeparableConv2D(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        >>> x = np.random.randn(32, 64, 56, 56)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 128, 56, 56)
    
    Use Case:
        MobileNet, Xception (efficient architectures)
    
    Reference:
        Chollet, "Xception" (2017)
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[int, Tuple[int, int]] = 0,
                 bias: bool = True):
        # Depthwise convolution
        self.depthwise = DepthwiseConv2D(in_channels, kernel_size, stride, padding, bias)
        
        # Pointwise convolution (1x1)
        self.pointwise = Conv2D(in_channels, out_channels, kernel_size=1, bias=bias)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        x = self.depthwise.forward(x)
        x = self.pointwise.forward(x)
        return x
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# DILATED CONV2D
# ============================================================================

class DilatedConv2D(Conv2D):
    """
    Dilated (Atrous) 2D Convolution.
    
    Expands receptive field without increasing parameters.
    Inserts gaps (dilation) between kernel elements.
    
    Receptive Field:
        Standard 3x3: 3x3
        Dilated 3x3 (rate=2): 5x5
        Dilated 3x3 (rate=3): 7x7
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        kernel_size: Size of convolution kernel
        stride: Stride of convolution (default: 1)
        padding: Padding to add (default: 0)
        dilation: Dilation rate (default: 2)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = DilatedConv2D(in_channels=64, out_channels=64, kernel_size=3, dilation=2, padding=2)
        >>> x = np.random.randn(32, 64, 56, 56)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 64, 56, 56)
    
    Use Case:
        Semantic segmentation (DeepLab), audio generation (WaveNet)
    
    Reference:
        Yu & Koltun, "Multi-Scale Context Aggregation by Dilated Convolutions" (2016)
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[int, Tuple[int, int]] = 0,
                 dilation: Union[int, Tuple[int, int]] = 2,
                 bias: bool = True):
        super().__init__(in_channels, out_channels, kernel_size, stride, padding, dilation, bias)


# ============================================================================
# TRANSPOSED CONV2D
# ============================================================================

class TransposedConv2D:
    """
    Transposed 2D Convolution (Deconvolution).
    
    Upsamples feature maps. Reverse of standard convolution.
    Used in decoders, GANs, segmentation.
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        kernel_size: Size of convolution kernel
        stride: Stride of convolution (default: 2 for 2x upsampling)
        padding: Padding to add (default: 0)
        output_padding: Additional output padding (default: 0)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = TransposedConv2D(in_channels=128, out_channels=64, kernel_size=4, stride=2, padding=1)
        >>> x = np.random.randn(32, 128, 28, 28)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 64, 56, 56) - 2x upsampling
    
    Use Case:
        U-Net, GANs, semantic segmentation (decoder)
    
    Reference:
        Zeiler et al., "Deconvolutional Networks" (2010)
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 2,
                 padding: Union[int, Tuple[int, int]] = 0,
                 output_padding: Union[int, Tuple[int, int]] = 0,
                 bias: bool = True):
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        if isinstance(kernel_size, int):
            self.kernel_h, self.kernel_w = kernel_size, kernel_size
        else:
            self.kernel_h, self.kernel_w = kernel_size
        
        if isinstance(stride, int):
            self.stride_h, self.stride_w = stride, stride
        else:
            self.stride_h, self.stride_w = stride
        
        if isinstance(padding, int):
            self.pad_h = self.pad_w = padding
        else:
            self.pad_h, self.pad_w = padding
        
        if isinstance(output_padding, int):
            self.out_pad_h = self.out_pad_w = output_padding
        else:
            self.out_pad_h, self.out_pad_w = output_padding
        
        self.use_bias = bias
        
        # Initialize weights
        self.weight = np.random.randn(in_channels, out_channels, self.kernel_h, self.kernel_w) * \
                     np.sqrt(2.0 / (in_channels * self.kernel_h * self.kernel_w))
        self.bias = np.zeros(out_channels) if bias else None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass (simplified implementation).
        
        Args:
            x: Input tensor (batch, in_channels, height, width)
        
        Returns:
            Upsampled output tensor
        """
        batch_size, in_channels, height, width = x.shape
        
        # Calculate output dimensions
        out_h = (height - 1) * self.stride_h - 2 * self.pad_h + self.kernel_h + self.out_pad_h
        out_w = (width - 1) * self.stride_w - 2 * self.pad_w + self.kernel_w + self.out_pad_w
        
        # Initialize output
        output = np.zeros((batch_size, self.out_channels, out_h, out_w))
        
        # Simplified transposed convolution
        for b in range(batch_size):
            for c_in in range(in_channels):
                for i in range(height):
                    for j in range(width):
                        h_start = i * self.stride_h
                        w_start = j * self.stride_w
                        
                        for c_out in range(self.out_channels):
                            for m in range(self.kernel_h):
                                for n in range(self.kernel_w):
                                    h_pos = h_start + m
                                    w_pos = w_start + n
                                    
                                    if 0 <= h_pos < out_h and 0 <= w_pos < out_w:
                                        output[b, c_out, h_pos, w_pos] += \
                                            x[b, c_in, i, j] * self.weight[c_in, c_out, m, n]
        
        # Add bias
        if self.use_bias:
            for c_out in range(self.out_channels):
                output[:, c_out, :, :] += self.bias[c_out]
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# CONV1X1
# ============================================================================

class Conv1x1(Conv2D):
    """
    1x1 Convolution (Pointwise Convolution).
    
    Channel mixing and dimensionality reduction/expansion.
    No spatial information, only channel-wise.
    
    Uses:
        - Dimensionality reduction (bottleneck)
        - Channel mixing
        - Adding non-linearity
        - Efficient feature combination
    
    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        bias: Whether to use bias (default: True)
    
    Example:
        >>> conv = Conv1x1(in_channels=256, out_channels=64)  # Reduce channels
        >>> x = np.random.randn(32, 256, 56, 56)
        >>> output = conv.forward(x)
        >>> print(output.shape)  # (32, 64, 56, 56)
    
    Use Case:
        ResNet bottleneck, Inception, channel reduction
    
    Reference:
        Lin et al., "Network In Network" (2013)
    """
    
    def __init__(self, in_channels: int, out_channels: int, bias: bool = True):
        super().__init__(in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=bias)


__all__ = [
    'Conv1D',
    'Conv2D',
    'Conv3D',
    'DepthwiseConv2D',
    'SeparableConv2D',
    'DilatedConv2D',
    'TransposedConv2D',
    'Conv1x1',
]
