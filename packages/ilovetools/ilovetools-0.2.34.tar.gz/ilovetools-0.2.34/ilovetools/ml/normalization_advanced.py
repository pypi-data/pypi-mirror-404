"""
Advanced Normalization Techniques

This module provides advanced normalization methods:
- Batch Normalization (BatchNorm)
- Layer Normalization (LayerNorm)
- Instance Normalization (InstanceNorm)
- Group Normalization (GroupNorm)
- Weight Normalization
- Spectral Normalization

All operations support batched inputs and are optimized for deep learning.
"""

import numpy as np
from typing import Tuple, Optional


# ============================================================================
# BATCH NORMALIZATION
# ============================================================================

def batch_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    running_mean: Optional[np.ndarray] = None,
    running_var: Optional[np.ndarray] = None,
    momentum: float = 0.9,
    eps: float = 1e-5,
    training: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Batch Normalization forward pass
    
    Normalizes across the batch dimension. Used in CNNs.
    
    Formula:
        μ_B = (1/m) Σ x_i
        σ²_B = (1/m) Σ (x_i - μ_B)²
        x̂ = (x - μ_B) / √(σ²_B + ε)
        y = γ x̂ + β
    
    Args:
        x: Input tensor, shape (batch, channels, height, width) or (batch, features)
        gamma: Scale parameter, shape (channels,) or (features,)
        beta: Shift parameter, shape (channels,) or (features,)
        running_mean: Running mean for inference
        running_var: Running variance for inference
        momentum: Momentum for running statistics
        eps: Small constant for numerical stability
        training: Whether in training mode
        
    Returns:
        Tuple of (output, updated_running_mean, updated_running_var)
        
    Example:
        >>> # For CNNs
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, H, W)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> output, mean, var = batch_norm_forward(x, gamma, beta, training=True)
        >>> print(output.shape)  # (32, 64, 28, 28)
        
        >>> # For fully connected
        >>> x = np.random.randn(32, 256)  # (batch, features)
        >>> gamma = np.ones(256)
        >>> beta = np.zeros(256)
        >>> output, mean, var = batch_norm_forward(x, gamma, beta, training=True)
        >>> print(output.shape)  # (32, 256)
    """
    if training:
        # Calculate batch statistics
        if x.ndim == 4:  # Conv: (batch, channels, height, width)
            # Mean and variance across batch, height, width
            axes = (0, 2, 3)
            mean = np.mean(x, axis=axes, keepdims=True)
            var = np.var(x, axis=axes, keepdims=True)
            
            # Squeeze for running stats
            mean_squeeze = np.squeeze(mean, axis=(0, 2, 3))
            var_squeeze = np.squeeze(var, axis=(0, 2, 3))
        else:  # FC: (batch, features)
            axes = 0
            mean = np.mean(x, axis=axes, keepdims=True)
            var = np.var(x, axis=axes, keepdims=True)
            
            mean_squeeze = np.squeeze(mean, axis=0)
            var_squeeze = np.squeeze(var, axis=0)
        
        # Update running statistics
        if running_mean is None:
            running_mean = mean_squeeze
        else:
            running_mean = momentum * running_mean + (1 - momentum) * mean_squeeze
            
        if running_var is None:
            running_var = var_squeeze
        else:
            running_var = momentum * running_var + (1 - momentum) * var_squeeze
        
        # Normalize
        x_normalized = (x - mean) / np.sqrt(var + eps)
    else:
        # Use running statistics for inference
        if running_mean is None or running_var is None:
            raise ValueError("Running statistics required for inference mode")
        
        if x.ndim == 4:
            mean = running_mean.reshape(1, -1, 1, 1)
            var = running_var.reshape(1, -1, 1, 1)
        else:
            mean = running_mean.reshape(1, -1)
            var = running_var.reshape(1, -1)
        
        x_normalized = (x - mean) / np.sqrt(var + eps)
    
    # Scale and shift
    if x.ndim == 4:
        gamma = gamma.reshape(1, -1, 1, 1)
        beta = beta.reshape(1, -1, 1, 1)
    else:
        gamma = gamma.reshape(1, -1)
        beta = beta.reshape(1, -1)
    
    output = gamma * x_normalized + beta
    
    return output, running_mean, running_var


# ============================================================================
# LAYER NORMALIZATION
# ============================================================================

def layer_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Layer Normalization forward pass
    
    Normalizes across the feature dimension. Used in Transformers and RNNs.
    
    Formula:
        μ = (1/H) Σ x_i
        σ² = (1/H) Σ (x_i - μ)²
        x̂ = (x - μ) / √(σ² + ε)
        y = γ x̂ + β
    
    Args:
        x: Input tensor, shape (batch, features) or (batch, seq_len, features)
        gamma: Scale parameter, shape (features,)
        beta: Shift parameter, shape (features,)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output with same shape as input
        
    Example:
        >>> # For Transformers
        >>> x = np.random.randn(32, 10, 512)  # (batch, seq_len, features)
        >>> gamma = np.ones(512)
        >>> beta = np.zeros(512)
        >>> output = layer_norm_forward(x, gamma, beta)
        >>> print(output.shape)  # (32, 10, 512)
        
        >>> # For fully connected
        >>> x = np.random.randn(32, 256)  # (batch, features)
        >>> gamma = np.ones(256)
        >>> beta = np.zeros(256)
        >>> output = layer_norm_forward(x, gamma, beta)
        >>> print(output.shape)  # (32, 256)
    """
    # Calculate mean and variance across feature dimension
    if x.ndim == 3:  # (batch, seq_len, features)
        axes = -1
        mean = np.mean(x, axis=axes, keepdims=True)
        var = np.var(x, axis=axes, keepdims=True)
    elif x.ndim == 2:  # (batch, features)
        axes = -1
        mean = np.mean(x, axis=axes, keepdims=True)
        var = np.var(x, axis=axes, keepdims=True)
    else:
        raise ValueError(f"Unsupported input shape: {x.shape}")
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + eps)
    
    # Scale and shift
    output = gamma * x_normalized + beta
    
    return output


# ============================================================================
# INSTANCE NORMALIZATION
# ============================================================================

def instance_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Instance Normalization forward pass
    
    Normalizes each sample and channel independently. Used in style transfer.
    
    Args:
        x: Input tensor, shape (batch, channels, height, width)
        gamma: Scale parameter, shape (channels,)
        beta: Shift parameter, shape (channels,)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output with same shape as input
        
    Example:
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, H, W)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> output = instance_norm_forward(x, gamma, beta)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    if x.ndim != 4:
        raise ValueError("Instance normalization requires 4D input (batch, channels, H, W)")
    
    # Calculate mean and variance per instance, per channel
    # Normalize across spatial dimensions (H, W)
    axes = (2, 3)
    mean = np.mean(x, axis=axes, keepdims=True)
    var = np.var(x, axis=axes, keepdims=True)
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + eps)
    
    # Scale and shift
    gamma = gamma.reshape(1, -1, 1, 1)
    beta = beta.reshape(1, -1, 1, 1)
    output = gamma * x_normalized + beta
    
    return output


# ============================================================================
# GROUP NORMALIZATION
# ============================================================================

def group_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    num_groups: int = 32,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Group Normalization forward pass
    
    Divides channels into groups and normalizes within each group.
    Good for small batch sizes.
    
    Args:
        x: Input tensor, shape (batch, channels, height, width)
        gamma: Scale parameter, shape (channels,)
        beta: Shift parameter, shape (channels,)
        num_groups: Number of groups to divide channels into
        eps: Small constant for numerical stability
        
    Returns:
        Normalized output with same shape as input
        
    Example:
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, H, W)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> output = group_norm_forward(x, gamma, beta, num_groups=32)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    if x.ndim != 4:
        raise ValueError("Group normalization requires 4D input (batch, channels, H, W)")
    
    batch_size, channels, height, width = x.shape
    
    if channels % num_groups != 0:
        raise ValueError(f"Number of channels ({channels}) must be divisible by num_groups ({num_groups})")
    
    # Reshape to separate groups
    x_grouped = x.reshape(batch_size, num_groups, channels // num_groups, height, width)
    
    # Calculate mean and variance per group
    axes = (2, 3, 4)
    mean = np.mean(x_grouped, axis=axes, keepdims=True)
    var = np.var(x_grouped, axis=axes, keepdims=True)
    
    # Normalize
    x_normalized = (x_grouped - mean) / np.sqrt(var + eps)
    
    # Reshape back
    x_normalized = x_normalized.reshape(batch_size, channels, height, width)
    
    # Scale and shift
    gamma = gamma.reshape(1, -1, 1, 1)
    beta = beta.reshape(1, -1, 1, 1)
    output = gamma * x_normalized + beta
    
    return output


# ============================================================================
# WEIGHT NORMALIZATION
# ============================================================================

def weight_norm(
    weight: np.ndarray,
    dim: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Weight Normalization
    
    Reparameterizes weight vectors to decouple magnitude and direction.
    
    Formula:
        w = g * (v / ||v||)
    
    Args:
        weight: Weight tensor
        dim: Dimension along which to compute norm
        
    Returns:
        Tuple of (normalized_weight, norm)
        
    Example:
        >>> weight = np.random.randn(64, 128)  # (out_features, in_features)
        >>> w_normalized, g = weight_norm(weight, dim=1)
        >>> print(w_normalized.shape)  # (64, 128)
        >>> print(g.shape)  # (64, 1)
    """
    # Calculate norm along specified dimension
    norm = np.linalg.norm(weight, axis=dim, keepdims=True)
    
    # Normalize
    normalized_weight = weight / (norm + 1e-8)
    
    return normalized_weight, norm


# ============================================================================
# SPECTRAL NORMALIZATION
# ============================================================================

def spectral_norm(
    weight: np.ndarray,
    num_iterations: int = 1
) -> np.ndarray:
    """
    Spectral Normalization
    
    Normalizes weight matrix by its largest singular value.
    Used in GANs for training stability.
    
    Args:
        weight: Weight tensor, shape (out_features, in_features)
        num_iterations: Number of power iterations
        
    Returns:
        Spectrally normalized weight
        
    Example:
        >>> weight = np.random.randn(64, 128)
        >>> w_normalized = spectral_norm(weight, num_iterations=1)
        >>> print(w_normalized.shape)  # (64, 128)
    """
    # Reshape weight to 2D if needed
    original_shape = weight.shape
    if weight.ndim > 2:
        weight = weight.reshape(weight.shape[0], -1)
    
    # Power iteration to estimate largest singular value
    u = np.random.randn(weight.shape[0])
    u = u / np.linalg.norm(u)
    
    for _ in range(num_iterations):
        v = np.dot(weight.T, u)
        v = v / np.linalg.norm(v)
        u = np.dot(weight, v)
        u = u / np.linalg.norm(u)
    
    # Calculate spectral norm (largest singular value)
    sigma = np.dot(u, np.dot(weight, v))
    
    # Normalize by spectral norm
    normalized_weight = weight / sigma
    
    # Reshape back to original shape
    normalized_weight = normalized_weight.reshape(original_shape)
    
    return normalized_weight


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def initialize_norm_params(
    num_features: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Initialize normalization parameters
    
    Args:
        num_features: Number of features/channels
        
    Returns:
        Tuple of (gamma, beta)
        - gamma: Scale parameter initialized to 1
        - beta: Shift parameter initialized to 0
        
    Example:
        >>> gamma, beta = initialize_norm_params(256)
        >>> print(gamma.shape, beta.shape)  # (256,) (256,)
    """
    gamma = np.ones(num_features)
    beta = np.zeros(num_features)
    return gamma, beta


def compute_norm_stats(
    x: np.ndarray,
    norm_type: str = 'batch'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute normalization statistics
    
    Args:
        x: Input tensor
        norm_type: Type of normalization ('batch', 'layer', 'instance', 'group')
        
    Returns:
        Tuple of (mean, variance)
        
    Example:
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> mean, var = compute_norm_stats(x, norm_type='batch')
        >>> print(mean.shape, var.shape)
    """
    if norm_type == 'batch':
        if x.ndim == 4:
            axes = (0, 2, 3)
        else:
            axes = 0
    elif norm_type == 'layer':
        axes = -1
    elif norm_type == 'instance':
        axes = (2, 3)
    else:
        raise ValueError(f"Unknown norm_type: {norm_type}")
    
    mean = np.mean(x, axis=axes, keepdims=True)
    var = np.var(x, axis=axes, keepdims=True)
    
    return mean, var


# Aliases for convenience
batch_norm = batch_norm_forward
layer_norm = layer_norm_forward
instance_norm = instance_norm_forward
group_norm = group_norm_forward
