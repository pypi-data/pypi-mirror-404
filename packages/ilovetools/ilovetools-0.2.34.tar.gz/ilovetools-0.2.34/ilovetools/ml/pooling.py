"""
Pooling Layers Suite

This module implements various pooling operations for neural networks.
Pooling layers reduce spatial dimensions while retaining important features,
providing translation invariance and reducing computational complexity.

Implemented Pooling Types:
1. MaxPool1D - 1D max pooling for sequences
2. MaxPool2D - 2D max pooling for images
3. AvgPool1D - 1D average pooling for sequences
4. AvgPool2D - 2D average pooling for images
5. GlobalMaxPool - Global max pooling (entire feature map)
6. GlobalAvgPool - Global average pooling (entire feature map)
7. AdaptiveMaxPool - Adaptive max pooling (fixed output size)
8. AdaptiveAvgPool - Adaptive average pooling (fixed output size)

References:
- Max Pooling: Standard practice in CNNs
- Global Pooling: "Network In Network" (Lin et al., 2013)
- Adaptive Pooling: PyTorch adaptive pooling layers

Author: Ali Mehdi
Date: January 17, 2026
"""

import numpy as np
from typing import Union, Tuple, Optional


class MaxPool1D:
    """
    1D Max Pooling Layer.
    
    Applies max pooling over 1D input (sequences, time series).
    Selects maximum value within each pooling window.
    
    Formula:
        output[i] = max(input[i*stride : i*stride + pool_size])
    
    Args:
        pool_size: Size of pooling window
        stride: Stride of pooling operation (default: pool_size)
        padding: Padding to add (default: 0)
    
    Example:
        >>> pool = MaxPool1D(pool_size=2, stride=2)
        >>> x = np.array([[[1, 3, 2, 4, 5, 1]]])  # (batch, channels, length)
        >>> output = pool.forward(x)
        >>> print(output)  # [[[3, 4, 5]]]
    
    Reference:
        Standard practice in CNNs
    """
    
    def __init__(self, pool_size: int, stride: Optional[int] = None, padding: int = 0):
        if pool_size <= 0:
            raise ValueError(f"pool_size must be positive, got {pool_size}")
        if padding < 0:
            raise ValueError(f"padding must be non-negative, got {padding}")
        
        self.pool_size = pool_size
        self.stride = stride if stride is not None else pool_size
        self.padding = padding
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, channels, length)
        
        Returns:
            Pooled output
        """
        batch_size, channels, length = x.shape
        
        # Apply padding
        if self.padding > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), (self.padding, self.padding)), 
                            mode='constant', constant_values=-np.inf)
        else:
            x_padded = x
        
        # Calculate output length
        out_length = (x_padded.shape[2] - self.pool_size) // self.stride + 1
        
        # Initialize output
        output = np.zeros((batch_size, channels, out_length))
        
        # Store for backward pass
        self.cache = (x.shape, x_padded)
        
        # Perform max pooling
        for i in range(out_length):
            start = i * self.stride
            end = start + self.pool_size
            output[:, :, i] = np.max(x_padded[:, :, start:end], axis=2)
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """
        Backward pass.
        
        Args:
            grad_output: Gradient from next layer
        
        Returns:
            Gradient w.r.t. input
        """
        x_shape, x_padded = self.cache
        batch_size, channels, length = x_shape
        
        # Initialize gradient
        grad_input = np.zeros_like(x_padded)
        
        out_length = grad_output.shape[2]
        
        # Backpropagate through max pooling
        for i in range(out_length):
            start = i * self.stride
            end = start + self.pool_size
            
            # Find max positions
            window = x_padded[:, :, start:end]
            max_vals = np.max(window, axis=2, keepdims=True)
            mask = (window == max_vals)
            
            # Distribute gradient to max positions
            grad_input[:, :, start:end] += mask * grad_output[:, :, i:i+1]
        
        # Remove padding
        if self.padding > 0:
            grad_input = grad_input[:, :, self.padding:-self.padding]
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class MaxPool2D:
    """
    2D Max Pooling Layer.
    
    Applies max pooling over 2D input (images, feature maps).
    Most common pooling operation in CNNs.
    
    Formula:
        output[i,j] = max(input[i*stride_h : i*stride_h + pool_h,
                               j*stride_w : j*stride_w + pool_w])
    
    Args:
        pool_size: Size of pooling window (int or tuple)
        stride: Stride of pooling operation (default: pool_size)
        padding: Padding to add (default: 0)
    
    Example:
        >>> pool = MaxPool2D(pool_size=2, stride=2)
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, height, width)
        >>> output = pool.forward(x)
        >>> print(output.shape)  # (32, 64, 14, 14)
    
    Reference:
        Standard practice in CNNs (AlexNet, VGG, ResNet)
    """
    
    def __init__(self, pool_size: Union[int, Tuple[int, int]], 
                 stride: Optional[Union[int, Tuple[int, int]]] = None,
                 padding: Union[int, Tuple[int, int]] = 0):
        # Handle pool_size
        if isinstance(pool_size, int):
            self.pool_h, self.pool_w = pool_size, pool_size
        else:
            self.pool_h, self.pool_w = pool_size
        
        # Handle stride
        if stride is None:
            self.stride_h, self.stride_w = self.pool_h, self.pool_w
        elif isinstance(stride, int):
            self.stride_h, self.stride_w = stride, stride
        else:
            self.stride_h, self.stride_w = stride
        
        # Handle padding
        if isinstance(padding, int):
            self.pad_h, self.pad_w = padding, padding
        else:
            self.pad_h, self.pad_w = padding
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, channels, height, width)
        
        Returns:
            Pooled output
        """
        batch_size, channels, height, width = x.shape
        
        # Apply padding
        if self.pad_h > 0 or self.pad_w > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), (self.pad_h, self.pad_h), 
                                (self.pad_w, self.pad_w)), 
                            mode='constant', constant_values=-np.inf)
        else:
            x_padded = x
        
        # Calculate output dimensions
        out_h = (x_padded.shape[2] - self.pool_h) // self.stride_h + 1
        out_w = (x_padded.shape[3] - self.pool_w) // self.stride_w + 1
        
        # Initialize output
        output = np.zeros((batch_size, channels, out_h, out_w))
        
        # Store for backward pass
        self.cache = (x.shape, x_padded)
        
        # Perform max pooling
        for i in range(out_h):
            for j in range(out_w):
                h_start = i * self.stride_h
                h_end = h_start + self.pool_h
                w_start = j * self.stride_w
                w_end = w_start + self.pool_w
                
                window = x_padded[:, :, h_start:h_end, w_start:w_end]
                output[:, :, i, j] = np.max(window, axis=(2, 3))
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x_shape, x_padded = self.cache
        batch_size, channels, height, width = x_shape
        
        grad_input = np.zeros_like(x_padded)
        out_h, out_w = grad_output.shape[2], grad_output.shape[3]
        
        for i in range(out_h):
            for j in range(out_w):
                h_start = i * self.stride_h
                h_end = h_start + self.pool_h
                w_start = j * self.stride_w
                w_end = w_start + self.pool_w
                
                window = x_padded[:, :, h_start:h_end, w_start:w_end]
                max_vals = np.max(window, axis=(2, 3), keepdims=True)
                mask = (window == max_vals)
                
                grad_input[:, :, h_start:h_end, w_start:w_end] += \
                    mask * grad_output[:, :, i:i+1, j:j+1]
        
        if self.pad_h > 0 or self.pad_w > 0:
            grad_input = grad_input[:, :, self.pad_h:-self.pad_h, self.pad_w:-self.pad_w]
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class AvgPool1D:
    """
    1D Average Pooling Layer.
    
    Applies average pooling over 1D input.
    Computes mean value within each pooling window.
    
    Formula:
        output[i] = mean(input[i*stride : i*stride + pool_size])
    
    Args:
        pool_size: Size of pooling window
        stride: Stride of pooling operation (default: pool_size)
        padding: Padding to add (default: 0)
    
    Example:
        >>> pool = AvgPool1D(pool_size=2, stride=2)
        >>> x = np.array([[[1, 3, 2, 4, 5, 1]]])
        >>> output = pool.forward(x)
        >>> print(output)  # [[[2.0, 3.0, 3.0]]]
    
    Reference:
        Standard practice in CNNs
    """
    
    def __init__(self, pool_size: int, stride: Optional[int] = None, padding: int = 0):
        if pool_size <= 0:
            raise ValueError(f"pool_size must be positive, got {pool_size}")
        
        self.pool_size = pool_size
        self.stride = stride if stride is not None else pool_size
        self.padding = padding
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, channels, length = x.shape
        
        if self.padding > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), (self.padding, self.padding)), 
                            mode='constant', constant_values=0)
        else:
            x_padded = x
        
        out_length = (x_padded.shape[2] - self.pool_size) // self.stride + 1
        output = np.zeros((batch_size, channels, out_length))
        
        self.cache = x.shape
        
        for i in range(out_length):
            start = i * self.stride
            end = start + self.pool_size
            output[:, :, i] = np.mean(x_padded[:, :, start:end], axis=2)
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x_shape = self.cache
        batch_size, channels, length = x_shape
        
        grad_input = np.zeros(x_shape)
        out_length = grad_output.shape[2]
        
        for i in range(out_length):
            start = i * self.stride
            end = start + self.pool_size
            
            # Distribute gradient equally
            grad_input[:, :, start:end] += grad_output[:, :, i:i+1] / self.pool_size
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class AvgPool2D:
    """
    2D Average Pooling Layer.
    
    Applies average pooling over 2D input.
    Smoother than max pooling, preserves more spatial information.
    
    Formula:
        output[i,j] = mean(input[i*stride_h : i*stride_h + pool_h,
                                 j*stride_w : j*stride_w + pool_w])
    
    Args:
        pool_size: Size of pooling window (int or tuple)
        stride: Stride of pooling operation (default: pool_size)
        padding: Padding to add (default: 0)
    
    Example:
        >>> pool = AvgPool2D(pool_size=2, stride=2)
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> output = pool.forward(x)
        >>> print(output.shape)  # (32, 64, 14, 14)
    
    Reference:
        Used in LeNet, some modern architectures
    """
    
    def __init__(self, pool_size: Union[int, Tuple[int, int]], 
                 stride: Optional[Union[int, Tuple[int, int]]] = None,
                 padding: Union[int, Tuple[int, int]] = 0):
        if isinstance(pool_size, int):
            self.pool_h, self.pool_w = pool_size, pool_size
        else:
            self.pool_h, self.pool_w = pool_size
        
        if stride is None:
            self.stride_h, self.stride_w = self.pool_h, self.pool_w
        elif isinstance(stride, int):
            self.stride_h, self.stride_w = stride, stride
        else:
            self.stride_h, self.stride_w = stride
        
        if isinstance(padding, int):
            self.pad_h, self.pad_w = padding, padding
        else:
            self.pad_h, self.pad_w = padding
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, channels, height, width = x.shape
        
        if self.pad_h > 0 or self.pad_w > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), (self.pad_h, self.pad_h), 
                                (self.pad_w, self.pad_w)), mode='constant')
        else:
            x_padded = x
        
        out_h = (x_padded.shape[2] - self.pool_h) // self.stride_h + 1
        out_w = (x_padded.shape[3] - self.pool_w) // self.stride_w + 1
        
        output = np.zeros((batch_size, channels, out_h, out_w))
        self.cache = x.shape
        
        for i in range(out_h):
            for j in range(out_w):
                h_start = i * self.stride_h
                h_end = h_start + self.pool_h
                w_start = j * self.stride_w
                w_end = w_start + self.pool_w
                
                window = x_padded[:, :, h_start:h_end, w_start:w_end]
                output[:, :, i, j] = np.mean(window, axis=(2, 3))
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x_shape = self.cache
        batch_size, channels, height, width = x_shape
        
        grad_input = np.zeros(x_shape)
        out_h, out_w = grad_output.shape[2], grad_output.shape[3]
        
        for i in range(out_h):
            for j in range(out_w):
                h_start = i * self.stride_h
                h_end = h_start + self.pool_h
                w_start = j * self.stride_w
                w_end = w_start + self.pool_w
                
                grad_input[:, :, h_start:h_end, w_start:w_end] += \
                    grad_output[:, :, i:i+1, j:j+1] / (self.pool_h * self.pool_w)
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class GlobalMaxPool:
    """
    Global Max Pooling Layer.
    
    Reduces each feature map to a single value by taking maximum.
    Commonly used before fully connected layers in classification.
    
    Formula:
        output[c] = max(input[:, c, :, :])
    
    Example:
        >>> pool = GlobalMaxPool()
        >>> x = np.random.randn(32, 512, 7, 7)  # (batch, channels, h, w)
        >>> output = pool.forward(x)
        >>> print(output.shape)  # (32, 512)
    
    Reference:
        "Network In Network" (Lin et al., 2013)
    """
    
    def __init__(self):
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, channels, height, width) or (batch, channels, length)
        
        Returns:
            Pooled output (batch, channels)
        """
        # Handle both 3D and 4D inputs
        if x.ndim == 3:
            # (batch, channels, length)
            output = np.max(x, axis=2)
        elif x.ndim == 4:
            # (batch, channels, height, width)
            output = np.max(x, axis=(2, 3))
        else:
            raise ValueError(f"Expected 3D or 4D input, got {x.ndim}D")
        
        self.cache = x
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x = self.cache
        
        if x.ndim == 3:
            max_vals = np.max(x, axis=2, keepdims=True)
            mask = (x == max_vals)
            grad_input = mask * grad_output[:, :, np.newaxis]
        else:
            max_vals = np.max(x, axis=(2, 3), keepdims=True)
            mask = (x == max_vals)
            grad_input = mask * grad_output[:, :, np.newaxis, np.newaxis]
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class GlobalAvgPool:
    """
    Global Average Pooling Layer.
    
    Reduces each feature map to a single value by averaging.
    Reduces overfitting compared to fully connected layers.
    
    Formula:
        output[c] = mean(input[:, c, :, :])
    
    Example:
        >>> pool = GlobalAvgPool()
        >>> x = np.random.randn(32, 512, 7, 7)
        >>> output = pool.forward(x)
        >>> print(output.shape)  # (32, 512)
    
    Reference:
        "Network In Network" (Lin et al., 2013)
        Used in ResNet, MobileNet, EfficientNet
    """
    
    def __init__(self):
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        if x.ndim == 3:
            output = np.mean(x, axis=2)
        elif x.ndim == 4:
            output = np.mean(x, axis=(2, 3))
        else:
            raise ValueError(f"Expected 3D or 4D input, got {x.ndim}D")
        
        self.cache = x
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x = self.cache
        
        if x.ndim == 3:
            spatial_size = x.shape[2]
            grad_input = np.repeat(grad_output[:, :, np.newaxis], spatial_size, axis=2)
            grad_input = grad_input / spatial_size
        else:
            spatial_size = x.shape[2] * x.shape[3]
            grad_input = np.repeat(np.repeat(grad_output[:, :, np.newaxis, np.newaxis], 
                                            x.shape[2], axis=2), x.shape[3], axis=3)
            grad_input = grad_input / spatial_size
        
        return grad_input
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class AdaptiveMaxPool:
    """
    Adaptive Max Pooling Layer.
    
    Pools to a fixed output size regardless of input size.
    Automatically calculates pooling parameters.
    
    Args:
        output_size: Desired output size (int or tuple)
    
    Example:
        >>> pool = AdaptiveMaxPool(output_size=(7, 7))
        >>> x1 = np.random.randn(32, 512, 14, 14)
        >>> x2 = np.random.randn(32, 512, 28, 28)
        >>> out1 = pool.forward(x1)
        >>> out2 = pool.forward(x2)
        >>> print(out1.shape, out2.shape)  # Both (32, 512, 7, 7)
    
    Reference:
        PyTorch AdaptiveMaxPool2d
    """
    
    def __init__(self, output_size: Union[int, Tuple[int, int]]):
        if isinstance(output_size, int):
            self.out_h, self.out_w = output_size, output_size
        else:
            self.out_h, self.out_w = output_size
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, channels, in_h, in_w = x.shape
        
        output = np.zeros((batch_size, channels, self.out_h, self.out_w))
        self.cache = x
        
        for i in range(self.out_h):
            for j in range(self.out_w):
                h_start = int(np.floor(i * in_h / self.out_h))
                h_end = int(np.ceil((i + 1) * in_h / self.out_h))
                w_start = int(np.floor(j * in_w / self.out_w))
                w_end = int(np.ceil((j + 1) * in_w / self.out_w))
                
                window = x[:, :, h_start:h_end, w_start:w_end]
                output[:, :, i, j] = np.max(window, axis=(2, 3))
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


class AdaptiveAvgPool:
    """
    Adaptive Average Pooling Layer.
    
    Pools to a fixed output size using averaging.
    
    Args:
        output_size: Desired output size (int or tuple)
    
    Example:
        >>> pool = AdaptiveAvgPool(output_size=(1, 1))  # Global avg pool
        >>> x = np.random.randn(32, 512, 14, 14)
        >>> output = pool.forward(x)
        >>> print(output.shape)  # (32, 512, 1, 1)
    
    Reference:
        PyTorch AdaptiveAvgPool2d
    """
    
    def __init__(self, output_size: Union[int, Tuple[int, int]]):
        if isinstance(output_size, int):
            self.out_h, self.out_w = output_size, output_size
        else:
            self.out_h, self.out_w = output_size
        
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, channels, in_h, in_w = x.shape
        
        output = np.zeros((batch_size, channels, self.out_h, self.out_w))
        self.cache = x
        
        for i in range(self.out_h):
            for j in range(self.out_w):
                h_start = int(np.floor(i * in_h / self.out_h))
                h_end = int(np.ceil((i + 1) * in_h / self.out_h))
                w_start = int(np.floor(j * in_w / self.out_w))
                w_end = int(np.ceil((j + 1) * in_w / self.out_w))
                
                window = x[:, :, h_start:h_end, w_start:w_end]
                output[:, :, i, j] = np.mean(window, axis=(2, 3))
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


__all__ = [
    'MaxPool1D',
    'MaxPool2D',
    'AvgPool1D',
    'AvgPool2D',
    'GlobalMaxPool',
    'GlobalAvgPool',
    'AdaptiveMaxPool',
    'AdaptiveAvgPool',
]
