"""
Batch Normalization and Layer Normalization

This module provides normalization techniques for deep neural networks:
- Batch Normalization (BatchNorm1d, BatchNorm2d)
- Layer Normalization
- Group Normalization
- Instance Normalization
- Running statistics management
- Learnable affine parameters

All operations support batched inputs and are optimized for deep learning.
"""

import numpy as np
from typing import Tuple, Optional, Dict


# ============================================================================
# BATCH NORMALIZATION
# ============================================================================

class BatchNorm1d:
    """
    Batch Normalization for 1D inputs (fully connected layers)
    
    Normalizes inputs across the batch dimension.
    
    Paper: "Batch Normalization: Accelerating Deep Network Training by 
           Reducing Internal Covariate Shift" (Ioffe & Szegedy, 2015)
    
    Formula:
        y = γ × (x - μ_B) / √(σ²_B + ε) + β
    
    Where:
        μ_B = batch mean
        σ²_B = batch variance
        γ, β = learnable scale and shift parameters
        ε = small constant for numerical stability
    
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.normalization import BatchNorm1d
        
        >>> # Initialize
        >>> bn = BatchNorm1d(num_features=128)
        
        >>> # Training
        >>> x = np.random.randn(32, 128)
        >>> output = bn.forward(x, training=True)
        >>> print(output.shape)  # (32, 128)
        
        >>> # Inference
        >>> x_test = np.random.randn(1, 128)
        >>> output = bn.forward(x_test, training=False)
    """
    
    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        momentum: float = 0.1,
        affine: bool = True,
        track_running_stats: bool = True
    ):
        """
        Initialize Batch Normalization
        
        Args:
            num_features: Number of features (C from input shape)
            eps: Small constant for numerical stability
            momentum: Momentum for running statistics
            affine: If True, learn γ and β parameters
            track_running_stats: If True, track running mean/var
        """
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats
        
        # Learnable parameters
        if affine:
            self.gamma = np.ones(num_features)
            self.beta = np.zeros(num_features)
        else:
            self.gamma = None
            self.beta = None
        
        # Running statistics
        if track_running_stats:
            self.running_mean = np.zeros(num_features)
            self.running_var = np.ones(num_features)
            self.num_batches_tracked = 0
        else:
            self.running_mean = None
            self.running_var = None
            self.num_batches_tracked = None
        
        # Cache for backward pass
        self.cache = {}
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Forward pass
        
        Args:
            x: Input tensor, shape (N, C) or (N, C, L)
            training: Whether in training mode
            
        Returns:
            Normalized output
        """
        if x.ndim == 2:
            # (N, C)
            return self._forward_2d(x, training)
        elif x.ndim == 3:
            # (N, C, L) - reshape to (N*L, C)
            N, C, L = x.shape
            x_reshaped = x.transpose(0, 2, 1).reshape(-1, C)
            output = self._forward_2d(x_reshaped, training)
            return output.reshape(N, L, C).transpose(0, 2, 1)
        else:
            raise ValueError(f"Expected 2D or 3D input, got {x.ndim}D")
    
    def _forward_2d(self, x: np.ndarray, training: bool) -> np.ndarray:
        """Forward pass for 2D input"""
        if training:
            # Compute batch statistics
            batch_mean = np.mean(x, axis=0)
            batch_var = np.var(x, axis=0)
            
            # Update running statistics
            if self.track_running_stats:
                self.running_mean = (1 - self.momentum) * self.running_mean + \
                                   self.momentum * batch_mean
                self.running_var = (1 - self.momentum) * self.running_var + \
                                  self.momentum * batch_var
                self.num_batches_tracked += 1
            
            # Normalize
            x_normalized = (x - batch_mean) / np.sqrt(batch_var + self.eps)
            
            # Cache for backward
            self.cache = {
                'x': x,
                'x_normalized': x_normalized,
                'batch_mean': batch_mean,
                'batch_var': batch_var
            }
        else:
            # Use running statistics
            if self.track_running_stats:
                x_normalized = (x - self.running_mean) / \
                              np.sqrt(self.running_var + self.eps)
            else:
                # Fallback to batch statistics
                batch_mean = np.mean(x, axis=0)
                batch_var = np.var(x, axis=0)
                x_normalized = (x - batch_mean) / np.sqrt(batch_var + self.eps)
        
        # Apply affine transformation
        if self.affine:
            output = self.gamma * x_normalized + self.beta
        else:
            output = x_normalized
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Backward pass
        
        Args:
            grad_output: Gradient of loss w.r.t. output
            
        Returns:
            Tuple of (grad_input, parameter_gradients)
        """
        x = self.cache['x']
        x_normalized = self.cache['x_normalized']
        batch_mean = self.cache['batch_mean']
        batch_var = self.cache['batch_var']
        
        N = x.shape[0]
        
        # Gradient w.r.t. gamma and beta
        if self.affine:
            grad_gamma = np.sum(grad_output * x_normalized, axis=0)
            grad_beta = np.sum(grad_output, axis=0)
            grad_x_normalized = grad_output * self.gamma
        else:
            grad_gamma = None
            grad_beta = None
            grad_x_normalized = grad_output
        
        # Gradient w.r.t. input
        std = np.sqrt(batch_var + self.eps)
        grad_var = np.sum(grad_x_normalized * (x - batch_mean) * -0.5 * std**(-3), axis=0)
        grad_mean = np.sum(grad_x_normalized * -1 / std, axis=0) + \
                   grad_var * np.mean(-2 * (x - batch_mean), axis=0)
        
        grad_x = grad_x_normalized / std + \
                grad_var * 2 * (x - batch_mean) / N + \
                grad_mean / N
        
        grads = {
            'gamma': grad_gamma,
            'beta': grad_beta
        }
        
        return grad_x, grads
    
    def reset_running_stats(self):
        """Reset running statistics"""
        if self.track_running_stats:
            self.running_mean = np.zeros(self.num_features)
            self.running_var = np.ones(self.num_features)
            self.num_batches_tracked = 0


class BatchNorm2d:
    """
    Batch Normalization for 2D inputs (convolutional layers)
    
    Normalizes inputs across batch and spatial dimensions.
    
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.normalization import BatchNorm2d
        
        >>> # Initialize
        >>> bn = BatchNorm2d(num_features=64)
        
        >>> # Training
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> output = bn.forward(x, training=True)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    
    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        momentum: float = 0.1,
        affine: bool = True,
        track_running_stats: bool = True
    ):
        """Initialize Batch Normalization for 2D"""
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats
        
        # Learnable parameters
        if affine:
            self.gamma = np.ones(num_features)
            self.beta = np.zeros(num_features)
        else:
            self.gamma = None
            self.beta = None
        
        # Running statistics
        if track_running_stats:
            self.running_mean = np.zeros(num_features)
            self.running_var = np.ones(num_features)
            self.num_batches_tracked = 0
        else:
            self.running_mean = None
            self.running_var = None
            self.num_batches_tracked = None
        
        self.cache = {}
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Forward pass
        
        Args:
            x: Input tensor, shape (N, C, H, W)
            training: Whether in training mode
            
        Returns:
            Normalized output
        """
        if x.ndim != 4:
            raise ValueError(f"Expected 4D input (N, C, H, W), got {x.ndim}D")
        
        N, C, H, W = x.shape
        
        if training:
            # Compute statistics across (N, H, W)
            batch_mean = np.mean(x, axis=(0, 2, 3))
            batch_var = np.var(x, axis=(0, 2, 3))
            
            # Update running statistics
            if self.track_running_stats:
                self.running_mean = (1 - self.momentum) * self.running_mean + \
                                   self.momentum * batch_mean
                self.running_var = (1 - self.momentum) * self.running_var + \
                                  self.momentum * batch_var
                self.num_batches_tracked += 1
            
            # Normalize
            x_normalized = (x - batch_mean.reshape(1, C, 1, 1)) / \
                          np.sqrt(batch_var.reshape(1, C, 1, 1) + self.eps)
            
            # Cache for backward
            self.cache = {
                'x': x,
                'x_normalized': x_normalized,
                'batch_mean': batch_mean,
                'batch_var': batch_var
            }
        else:
            # Use running statistics
            if self.track_running_stats:
                x_normalized = (x - self.running_mean.reshape(1, C, 1, 1)) / \
                              np.sqrt(self.running_var.reshape(1, C, 1, 1) + self.eps)
            else:
                batch_mean = np.mean(x, axis=(0, 2, 3))
                batch_var = np.var(x, axis=(0, 2, 3))
                x_normalized = (x - batch_mean.reshape(1, C, 1, 1)) / \
                              np.sqrt(batch_var.reshape(1, C, 1, 1) + self.eps)
        
        # Apply affine transformation
        if self.affine:
            output = self.gamma.reshape(1, C, 1, 1) * x_normalized + \
                    self.beta.reshape(1, C, 1, 1)
        else:
            output = x_normalized
        
        return output
    
    def reset_running_stats(self):
        """Reset running statistics"""
        if self.track_running_stats:
            self.running_mean = np.zeros(self.num_features)
            self.running_var = np.ones(self.num_features)
            self.num_batches_tracked = 0


# ============================================================================
# LAYER NORMALIZATION
# ============================================================================

class LayerNorm:
    """
    Layer Normalization
    
    Normalizes inputs across the feature dimension (per sample).
    
    Paper: "Layer Normalization" (Ba et al., 2016)
    
    Formula:
        y = γ × (x - μ_L) / √(σ²_L + ε) + β
    
    Where:
        μ_L = mean across features (per sample)
        σ²_L = variance across features (per sample)
        γ, β = learnable scale and shift parameters
    
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.normalization import LayerNorm
        
        >>> # Initialize
        >>> ln = LayerNorm(normalized_shape=512)
        
        >>> # Forward pass (same for training and inference)
        >>> x = np.random.randn(32, 10, 512)  # (batch, seq_len, features)
        >>> output = ln.forward(x)
        >>> print(output.shape)  # (32, 10, 512)
    """
    
    def __init__(
        self,
        normalized_shape: int,
        eps: float = 1e-5,
        elementwise_affine: bool = True
    ):
        """
        Initialize Layer Normalization
        
        Args:
            normalized_shape: Size of the feature dimension
            eps: Small constant for numerical stability
            elementwise_affine: If True, learn γ and β parameters
        """
        self.normalized_shape = normalized_shape
        self.eps = eps
        self.elementwise_affine = elementwise_affine
        
        # Learnable parameters
        if elementwise_affine:
            self.gamma = np.ones(normalized_shape)
            self.beta = np.zeros(normalized_shape)
        else:
            self.gamma = None
            self.beta = None
        
        self.cache = {}
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass
        
        Args:
            x: Input tensor, shape (..., normalized_shape)
            
        Returns:
            Normalized output
        """
        # Compute statistics across last dimension
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        
        # Normalize
        x_normalized = (x - mean) / np.sqrt(var + self.eps)
        
        # Cache for backward
        self.cache = {
            'x': x,
            'x_normalized': x_normalized,
            'mean': mean,
            'var': var
        }
        
        # Apply affine transformation
        if self.elementwise_affine:
            output = self.gamma * x_normalized + self.beta
        else:
            output = x_normalized
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Backward pass
        
        Args:
            grad_output: Gradient of loss w.r.t. output
            
        Returns:
            Tuple of (grad_input, parameter_gradients)
        """
        x = self.cache['x']
        x_normalized = self.cache['x_normalized']
        mean = self.cache['mean']
        var = self.cache['var']
        
        D = self.normalized_shape
        
        # Gradient w.r.t. gamma and beta
        if self.elementwise_affine:
            grad_gamma = np.sum(grad_output * x_normalized, axis=tuple(range(grad_output.ndim - 1)))
            grad_beta = np.sum(grad_output, axis=tuple(range(grad_output.ndim - 1)))
            grad_x_normalized = grad_output * self.gamma
        else:
            grad_gamma = None
            grad_beta = None
            grad_x_normalized = grad_output
        
        # Gradient w.r.t. input
        std = np.sqrt(var + self.eps)
        grad_var = np.sum(grad_x_normalized * (x - mean) * -0.5 * std**(-3), axis=-1, keepdims=True)
        grad_mean = np.sum(grad_x_normalized * -1 / std, axis=-1, keepdims=True) + \
                   grad_var * np.mean(-2 * (x - mean), axis=-1, keepdims=True)
        
        grad_x = grad_x_normalized / std + \
                grad_var * 2 * (x - mean) / D + \
                grad_mean / D
        
        grads = {
            'gamma': grad_gamma,
            'beta': grad_beta
        }
        
        return grad_x, grads


# ============================================================================
# GROUP NORMALIZATION
# ============================================================================

class GroupNorm:
    """
    Group Normalization
    
    Divides channels into groups and normalizes within each group.
    
    Paper: "Group Normalization" (Wu & He, 2018)
    
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.normalization import GroupNorm
        
        >>> # Initialize (64 channels, 8 groups)
        >>> gn = GroupNorm(num_groups=8, num_channels=64)
        
        >>> # Forward pass
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> output = gn.forward(x)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    
    def __init__(
        self,
        num_groups: int,
        num_channels: int,
        eps: float = 1e-5,
        affine: bool = True
    ):
        """
        Initialize Group Normalization
        
        Args:
            num_groups: Number of groups to divide channels into
            num_channels: Number of channels
            eps: Small constant for numerical stability
            affine: If True, learn γ and β parameters
        """
        if num_channels % num_groups != 0:
            raise ValueError(f"num_channels ({num_channels}) must be divisible by num_groups ({num_groups})")
        
        self.num_groups = num_groups
        self.num_channels = num_channels
        self.eps = eps
        self.affine = affine
        
        # Learnable parameters
        if affine:
            self.gamma = np.ones(num_channels)
            self.beta = np.zeros(num_channels)
        else:
            self.gamma = None
            self.beta = None
        
        self.cache = {}
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass
        
        Args:
            x: Input tensor, shape (N, C, H, W)
            
        Returns:
            Normalized output
        """
        if x.ndim != 4:
            raise ValueError(f"Expected 4D input (N, C, H, W), got {x.ndim}D")
        
        N, C, H, W = x.shape
        
        # Reshape to (N, G, C//G, H, W)
        x_grouped = x.reshape(N, self.num_groups, C // self.num_groups, H, W)
        
        # Compute statistics per group
        mean = np.mean(x_grouped, axis=(2, 3, 4), keepdims=True)
        var = np.var(x_grouped, axis=(2, 3, 4), keepdims=True)
        
        # Normalize
        x_normalized = (x_grouped - mean) / np.sqrt(var + self.eps)
        
        # Reshape back
        x_normalized = x_normalized.reshape(N, C, H, W)
        
        # Cache for backward
        self.cache = {
            'x': x,
            'x_normalized': x_normalized,
            'mean': mean,
            'var': var
        }
        
        # Apply affine transformation
        if self.affine:
            output = self.gamma.reshape(1, C, 1, 1) * x_normalized + \
                    self.beta.reshape(1, C, 1, 1)
        else:
            output = x_normalized
        
        return output


# ============================================================================
# INSTANCE NORMALIZATION
# ============================================================================

class InstanceNorm:
    """
    Instance Normalization
    
    Normalizes each sample and channel independently.
    
    Paper: "Instance Normalization: The Missing Ingredient for Fast Stylization" 
           (Ulyanov et al., 2016)
    
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.normalization import InstanceNorm
        
        >>> # Initialize
        >>> in_norm = InstanceNorm(num_features=64)
        
        >>> # Forward pass
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> output = in_norm.forward(x)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    
    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        affine: bool = True
    ):
        """
        Initialize Instance Normalization
        
        Args:
            num_features: Number of features/channels
            eps: Small constant for numerical stability
            affine: If True, learn γ and β parameters
        """
        self.num_features = num_features
        self.eps = eps
        self.affine = affine
        
        # Learnable parameters
        if affine:
            self.gamma = np.ones(num_features)
            self.beta = np.zeros(num_features)
        else:
            self.gamma = None
            self.beta = None
        
        self.cache = {}
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass
        
        Args:
            x: Input tensor, shape (N, C, H, W)
            
        Returns:
            Normalized output
        """
        if x.ndim != 4:
            raise ValueError(f"Expected 4D input (N, C, H, W), got {x.ndim}D")
        
        N, C, H, W = x.shape
        
        # Compute statistics per instance and channel
        mean = np.mean(x, axis=(2, 3), keepdims=True)
        var = np.var(x, axis=(2, 3), keepdims=True)
        
        # Normalize
        x_normalized = (x - mean) / np.sqrt(var + self.eps)
        
        # Cache for backward
        self.cache = {
            'x': x,
            'x_normalized': x_normalized,
            'mean': mean,
            'var': var
        }
        
        # Apply affine transformation
        if self.affine:
            output = self.gamma.reshape(1, C, 1, 1) * x_normalized + \
                    self.beta.reshape(1, C, 1, 1)
        else:
            output = x_normalized
        
        return output


# ============================================================================
# FUNCTIONAL API
# ============================================================================

def batch_norm_1d(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    running_mean: Optional[np.ndarray] = None,
    running_var: Optional[np.ndarray] = None,
    training: bool = True,
    momentum: float = 0.1,
    eps: float = 1e-5
) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Functional batch normalization for 1D inputs
    
    Args:
        x: Input tensor, shape (N, C)
        gamma: Scale parameter, shape (C,)
        beta: Shift parameter, shape (C,)
        running_mean: Running mean, shape (C,)
        running_var: Running variance, shape (C,)
        training: Whether in training mode
        momentum: Momentum for running statistics
        eps: Small constant for numerical stability
        
    Returns:
        Tuple of (output, updated_running_mean, updated_running_var)
    """
    if training:
        # Compute batch statistics
        batch_mean = np.mean(x, axis=0)
        batch_var = np.var(x, axis=0)
        
        # Update running statistics
        if running_mean is not None and running_var is not None:
            running_mean = (1 - momentum) * running_mean + momentum * batch_mean
            running_var = (1 - momentum) * running_var + momentum * batch_var
        
        # Normalize
        x_normalized = (x - batch_mean) / np.sqrt(batch_var + eps)
    else:
        # Use running statistics
        if running_mean is None or running_var is None:
            raise ValueError("Running statistics required for inference mode")
        x_normalized = (x - running_mean) / np.sqrt(running_var + eps)
    
    # Apply affine transformation
    output = gamma * x_normalized + beta
    
    return output, running_mean, running_var


def layer_norm(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Functional layer normalization
    
    Args:
        x: Input tensor, shape (..., D)
        gamma: Scale parameter, shape (D,)
        beta: Shift parameter, shape (D,)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output
    """
    # Compute statistics across last dimension
    mean = np.mean(x, axis=-1, keepdims=True)
    var = np.var(x, axis=-1, keepdims=True)
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + eps)
    
    # Apply affine transformation
    output = gamma * x_normalized + beta
    
    return output


def group_norm(
    x: np.ndarray,
    num_groups: int,
    gamma: np.ndarray,
    beta: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Functional group normalization
    
    Args:
        x: Input tensor, shape (N, C, H, W)
        num_groups: Number of groups
        gamma: Scale parameter, shape (C,)
        beta: Shift parameter, shape (C,)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output
    """
    N, C, H, W = x.shape
    
    # Reshape to (N, G, C//G, H, W)
    x_grouped = x.reshape(N, num_groups, C // num_groups, H, W)
    
    # Compute statistics per group
    mean = np.mean(x_grouped, axis=(2, 3, 4), keepdims=True)
    var = np.var(x_grouped, axis=(2, 3, 4), keepdims=True)
    
    # Normalize
    x_normalized = (x_grouped - mean) / np.sqrt(var + eps)
    
    # Reshape back
    x_normalized = x_normalized.reshape(N, C, H, W)
    
    # Apply affine transformation
    output = gamma.reshape(1, C, 1, 1) * x_normalized + beta.reshape(1, C, 1, 1)
    
    return output


def instance_norm(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Functional instance normalization
    
    Args:
        x: Input tensor, shape (N, C, H, W)
        gamma: Scale parameter, shape (C,)
        beta: Shift parameter, shape (C,)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output
    """
    N, C, H, W = x.shape
    
    # Compute statistics per instance and channel
    mean = np.mean(x, axis=(2, 3), keepdims=True)
    var = np.var(x, axis=(2, 3), keepdims=True)
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + eps)
    
    # Apply affine transformation
    output = gamma.reshape(1, C, 1, 1) * x_normalized + beta.reshape(1, C, 1, 1)
    
    return output


# Aliases
batchnorm1d = batch_norm_1d
layernorm = layer_norm
groupnorm = group_norm
instancenorm = instance_norm
batch_normalization = batch_norm_1d
layer_normalization = layer_norm
