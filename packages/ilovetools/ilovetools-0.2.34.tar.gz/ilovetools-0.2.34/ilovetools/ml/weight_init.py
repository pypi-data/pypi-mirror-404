"""
Weight Initialization Techniques Module

This module provides comprehensive implementations of weight initialization
strategies for training deep neural networks effectively.

Features:
- Xavier/Glorot Initialization (Uniform & Normal)
- He/Kaiming Initialization (Uniform & Normal)
- LeCun Initialization (Uniform & Normal)
- Orthogonal Initialization
- Identity Initialization
- Sparse Initialization
- Variance Scaling (Generalized)
- Constant Initialization
- Uniform Initialization
- Normal Initialization

Author: Ali Mehdi
License: MIT
"""

import numpy as np
from typing import Tuple, Optional, Union


# ============================================================================
# XAVIER/GLOROT INITIALIZATION
# ============================================================================

def xavier_uniform(shape: Tuple[int, ...], gain: float = 1.0) -> np.ndarray:
    """
    Xavier/Glorot Uniform Initialization
    
    Samples weights from uniform distribution U(-a, a) where:
    a = gain * sqrt(6 / (fan_in + fan_out))
    
    Best for: sigmoid, tanh activations
    
    Args:
        shape: Shape of weight tensor (e.g., (input_size, output_size))
        gain: Scaling factor (default: 1.0)
    
    Returns:
        Initialized weight array
    
    Reference:
        "Understanding the difficulty of training deep feedforward neural networks"
        - Glorot & Bengio (2010)
    """
    fan_in, fan_out = _calculate_fan_in_fan_out(shape)
    std = gain * np.sqrt(6.0 / (fan_in + fan_out))
    return np.random.uniform(-std, std, size=shape)


def xavier_normal(shape: Tuple[int, ...], gain: float = 1.0) -> np.ndarray:
    """
    Xavier/Glorot Normal Initialization
    
    Samples weights from normal distribution N(0, std^2) where:
    std = gain * sqrt(2 / (fan_in + fan_out))
    
    Best for: sigmoid, tanh activations
    
    Args:
        shape: Shape of weight tensor
        gain: Scaling factor (default: 1.0)
    
    Returns:
        Initialized weight array
    """
    fan_in, fan_out = _calculate_fan_in_fan_out(shape)
    std = gain * np.sqrt(2.0 / (fan_in + fan_out))
    return np.random.normal(0, std, size=shape)


# ============================================================================
# HE/KAIMING INITIALIZATION
# ============================================================================

def he_uniform(shape: Tuple[int, ...], gain: float = np.sqrt(2.0)) -> np.ndarray:
    """
    He/Kaiming Uniform Initialization
    
    Samples weights from uniform distribution U(-a, a) where:
    a = gain * sqrt(3 / fan_in)
    
    Best for: ReLU, LeakyReLU, PReLU activations
    
    Args:
        shape: Shape of weight tensor
        gain: Scaling factor (default: sqrt(2) for ReLU)
    
    Returns:
        Initialized weight array
    
    Reference:
        "Delving Deep into Rectifiers: Surpassing Human-Level Performance"
        - He et al. (2015)
    """
    fan_in, _ = _calculate_fan_in_fan_out(shape)
    std = gain * np.sqrt(3.0 / fan_in)
    return np.random.uniform(-std, std, size=shape)


def he_normal(shape: Tuple[int, ...], gain: float = np.sqrt(2.0)) -> np.ndarray:
    """
    He/Kaiming Normal Initialization
    
    Samples weights from normal distribution N(0, std^2) where:
    std = gain * sqrt(1 / fan_in)
    
    Best for: ReLU, LeakyReLU, PReLU activations
    
    Args:
        shape: Shape of weight tensor
        gain: Scaling factor (default: sqrt(2) for ReLU)
    
    Returns:
        Initialized weight array
    """
    fan_in, _ = _calculate_fan_in_fan_out(shape)
    std = gain / np.sqrt(fan_in)
    return np.random.normal(0, std, size=shape)


# ============================================================================
# LECUN INITIALIZATION
# ============================================================================

def lecun_uniform(shape: Tuple[int, ...]) -> np.ndarray:
    """
    LeCun Uniform Initialization
    
    Samples weights from uniform distribution U(-a, a) where:
    a = sqrt(3 / fan_in)
    
    Best for: SELU activation (self-normalizing networks)
    
    Args:
        shape: Shape of weight tensor
    
    Returns:
        Initialized weight array
    
    Reference:
        "Efficient BackProp" - LeCun et al. (1998)
    """
    fan_in, _ = _calculate_fan_in_fan_out(shape)
    std = np.sqrt(3.0 / fan_in)
    return np.random.uniform(-std, std, size=shape)


def lecun_normal(shape: Tuple[int, ...]) -> np.ndarray:
    """
    LeCun Normal Initialization
    
    Samples weights from normal distribution N(0, std^2) where:
    std = sqrt(1 / fan_in)
    
    Best for: SELU activation (self-normalizing networks)
    
    Args:
        shape: Shape of weight tensor
    
    Returns:
        Initialized weight array
    """
    fan_in, _ = _calculate_fan_in_fan_out(shape)
    std = 1.0 / np.sqrt(fan_in)
    return np.random.normal(0, std, size=shape)


# ============================================================================
# ORTHOGONAL INITIALIZATION
# ============================================================================

def orthogonal(shape: Tuple[int, ...], gain: float = 1.0) -> np.ndarray:
    """
    Orthogonal Initialization
    
    Initializes weights as (semi-)orthogonal matrix.
    Useful for RNNs and very deep networks.
    
    Args:
        shape: Shape of weight tensor
        gain: Scaling factor (default: 1.0)
    
    Returns:
        Initialized weight array
    
    Reference:
        "Exact solutions to the nonlinear dynamics of learning in deep linear neural networks"
        - Saxe et al. (2013)
    """
    if len(shape) < 2:
        raise ValueError("Orthogonal initialization requires at least 2D tensor")
    
    # Flatten to 2D
    rows = shape[0]
    cols = np.prod(shape[1:])
    flat_shape = (rows, cols)
    
    # Generate random matrix
    a = np.random.normal(0, 1, flat_shape)
    
    # QR decomposition
    q, r = np.linalg.qr(a)
    
    # Make Q uniform
    d = np.diag(r)
    q *= np.sign(d)
    
    # Scale by gain
    q *= gain
    
    # Reshape to original shape
    return q.reshape(shape)


# ============================================================================
# VARIANCE SCALING INITIALIZATION
# ============================================================================

def variance_scaling(
    shape: Tuple[int, ...],
    scale: float = 1.0,
    mode: str = 'fan_in',
    distribution: str = 'normal'
) -> np.ndarray:
    """
    Variance Scaling Initialization (Generalized)
    
    Flexible initialization that generalizes Xavier and He methods.
    
    Args:
        shape: Shape of weight tensor
        scale: Scaling factor
        mode: 'fan_in', 'fan_out', or 'fan_avg'
        distribution: 'normal' or 'uniform'
    
    Returns:
        Initialized weight array
    
    Examples:
        Xavier Normal: variance_scaling(shape, scale=1.0, mode='fan_avg')
        He Normal: variance_scaling(shape, scale=2.0, mode='fan_in')
    """
    fan_in, fan_out = _calculate_fan_in_fan_out(shape)
    
    if mode == 'fan_in':
        denominator = fan_in
    elif mode == 'fan_out':
        denominator = fan_out
    elif mode == 'fan_avg':
        denominator = (fan_in + fan_out) / 2.0
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    variance = scale / denominator
    
    if distribution == 'normal':
        std = np.sqrt(variance)
        return np.random.normal(0, std, size=shape)
    elif distribution == 'uniform':
        limit = np.sqrt(3.0 * variance)
        return np.random.uniform(-limit, limit, size=shape)
    else:
        raise ValueError(f"Invalid distribution: {distribution}")


# ============================================================================
# SPARSE INITIALIZATION
# ============================================================================

def sparse(shape: Tuple[int, ...], sparsity: float = 0.1, std: float = 0.01) -> np.ndarray:
    """
    Sparse Initialization
    
    Initializes weights with specified sparsity (fraction of zeros).
    Non-zero weights are sampled from N(0, std^2).
    
    Args:
        shape: Shape of weight tensor
        sparsity: Fraction of weights to set to zero (0 to 1)
        std: Standard deviation for non-zero weights
    
    Returns:
        Initialized weight array
    """
    if not 0 <= sparsity <= 1:
        raise ValueError("Sparsity must be between 0 and 1")
    
    weights = np.random.normal(0, std, size=shape)
    mask = np.random.random(shape) < sparsity
    weights[mask] = 0
    return weights


# ============================================================================
# IDENTITY INITIALIZATION
# ============================================================================

def identity(shape: Tuple[int, ...], gain: float = 1.0) -> np.ndarray:
    """
    Identity Initialization
    
    Initializes weights as identity matrix (or close to it).
    Useful for residual connections and skip connections.
    
    Args:
        shape: Shape of weight tensor (must be square or have square leading dims)
        gain: Scaling factor
    
    Returns:
        Initialized weight array
    """
    if len(shape) < 2:
        raise ValueError("Identity initialization requires at least 2D tensor")
    
    if shape[0] != shape[1]:
        raise ValueError("Identity initialization requires square matrix")
    
    weights = np.eye(shape[0], shape[1]) * gain
    
    # If more dimensions, tile the identity
    if len(shape) > 2:
        weights = np.tile(weights.reshape(shape[0], shape[1], 1), 
                         (1, 1) + shape[2:])
    
    return weights


# ============================================================================
# SIMPLE INITIALIZATIONS
# ============================================================================

def constant(shape: Tuple[int, ...], value: float = 0.0) -> np.ndarray:
    """
    Constant Initialization
    
    Initializes all weights to a constant value.
    
    Args:
        shape: Shape of weight tensor
        value: Constant value (default: 0.0)
    
    Returns:
        Initialized weight array
    """
    return np.full(shape, value, dtype=np.float32)


def uniform(shape: Tuple[int, ...], low: float = -0.05, high: float = 0.05) -> np.ndarray:
    """
    Uniform Initialization
    
    Samples weights uniformly from [low, high].
    
    Args:
        shape: Shape of weight tensor
        low: Lower bound
        high: Upper bound
    
    Returns:
        Initialized weight array
    """
    return np.random.uniform(low, high, size=shape)


def normal(shape: Tuple[int, ...], mean: float = 0.0, std: float = 0.01) -> np.ndarray:
    """
    Normal Initialization
    
    Samples weights from normal distribution N(mean, std^2).
    
    Args:
        shape: Shape of weight tensor
        mean: Mean of distribution
        std: Standard deviation
    
    Returns:
        Initialized weight array
    """
    return np.random.normal(mean, std, size=shape)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _calculate_fan_in_fan_out(shape: Tuple[int, ...]) -> Tuple[int, int]:
    """
    Calculate fan_in and fan_out for a weight tensor
    
    Args:
        shape: Shape of weight tensor
    
    Returns:
        Tuple of (fan_in, fan_out)
    """
    if len(shape) < 2:
        raise ValueError("Weight tensor must have at least 2 dimensions")
    
    if len(shape) == 2:
        # Fully connected layer
        fan_in = shape[0]
        fan_out = shape[1]
    else:
        # Convolutional layer: (out_channels, in_channels, kernel_h, kernel_w)
        receptive_field_size = np.prod(shape[2:])
        fan_in = shape[1] * receptive_field_size
        fan_out = shape[0] * receptive_field_size
    
    return fan_in, fan_out


def calculate_gain(activation: str) -> float:
    """
    Calculate recommended gain for different activation functions
    
    Args:
        activation: Name of activation function
    
    Returns:
        Recommended gain value
    """
    gains = {
        'linear': 1.0,
        'sigmoid': 1.0,
        'tanh': 5.0 / 3.0,
        'relu': np.sqrt(2.0),
        'leaky_relu': np.sqrt(2.0 / (1 + 0.01**2)),
        'selu': 1.0,
    }
    
    activation = activation.lower()
    if activation not in gains:
        raise ValueError(f"Unknown activation: {activation}")
    
    return gains[activation]


def get_initializer(
    method: str,
    shape: Tuple[int, ...],
    **kwargs
) -> np.ndarray:
    """
    Factory function to get initializer by name
    
    Args:
        method: Name of initialization method
        shape: Shape of weight tensor
        **kwargs: Additional method-specific arguments
    
    Returns:
        Initialized weight array
    """
    initializers = {
        'xavier_uniform': xavier_uniform,
        'xavier_normal': xavier_normal,
        'glorot_uniform': xavier_uniform,
        'glorot_normal': xavier_normal,
        'he_uniform': he_uniform,
        'he_normal': he_normal,
        'kaiming_uniform': he_uniform,
        'kaiming_normal': he_normal,
        'lecun_uniform': lecun_uniform,
        'lecun_normal': lecun_normal,
        'orthogonal': orthogonal,
        'identity': identity,
        'sparse': sparse,
        'constant': constant,
        'uniform': uniform,
        'normal': normal,
        'variance_scaling': variance_scaling,
    }
    
    method = method.lower()
    if method not in initializers:
        raise ValueError(f"Unknown initialization method: {method}")
    
    return initializers[method](shape, **kwargs)


# ============================================================================
# WEIGHT INITIALIZER CLASS
# ============================================================================

class WeightInitializer:
    """
    Weight Initializer Class
    
    Provides a convenient interface for weight initialization
    with support for different methods and configurations.
    """
    
    def __init__(self, method: str = 'xavier_normal', **kwargs):
        """
        Initialize WeightInitializer
        
        Args:
            method: Initialization method name
            **kwargs: Method-specific parameters
        """
        self.method = method
        self.kwargs = kwargs
    
    def initialize(self, shape: Tuple[int, ...]) -> np.ndarray:
        """
        Initialize weights with specified shape
        
        Args:
            shape: Shape of weight tensor
        
        Returns:
            Initialized weight array
        """
        return get_initializer(self.method, shape, **self.kwargs)
    
    def __call__(self, shape: Tuple[int, ...]) -> np.ndarray:
        """Allow calling instance as function"""
        return self.initialize(shape)


# ============================================================================
# ALIASES FOR CONVENIENCE
# ============================================================================

glorot_uniform = xavier_uniform
glorot_normal = xavier_normal
kaiming_uniform = he_uniform
kaiming_normal = he_normal


__all__ = [
    # Xavier/Glorot
    'xavier_uniform',
    'xavier_normal',
    'glorot_uniform',
    'glorot_normal',
    # He/Kaiming
    'he_uniform',
    'he_normal',
    'kaiming_uniform',
    'kaiming_normal',
    # LeCun
    'lecun_uniform',
    'lecun_normal',
    # Advanced
    'orthogonal',
    'identity',
    'sparse',
    'variance_scaling',
    # Simple
    'constant',
    'uniform',
    'normal',
    # Utilities
    'calculate_gain',
    'get_initializer',
    'WeightInitializer',
]
