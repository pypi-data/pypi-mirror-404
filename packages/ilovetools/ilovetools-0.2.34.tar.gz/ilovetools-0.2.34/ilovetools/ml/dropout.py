"""
Dropout Regularization Techniques

This module implements various dropout regularization techniques for preventing
overfitting in neural networks. Dropout randomly deactivates neurons during training,
forcing the network to learn more robust features.

Implemented Techniques:
1. Standard Dropout - Random neuron dropout
2. Spatial Dropout (Dropout2D) - Drops entire feature maps
3. Spatial Dropout 3D (Dropout3D) - Drops entire 3D feature maps
4. Variational Dropout - Same mask across time steps
5. DropConnect - Drops connections instead of neurons
6. Alpha Dropout - Maintains mean and variance (for SELU)

References:
- "Dropout: A Simple Way to Prevent Neural Networks from Overfitting" (Srivastava et al., 2014)
- "Efficient Object Localization Using Convolutional Networks" (Tompson et al., 2015)
- "Variational Dropout and the Local Reparameterization Trick" (Kingma et al., 2015)
- "Regularization of Neural Networks using DropConnect" (Wan et al., 2013)
- "Self-Normalizing Neural Networks" (Klambauer et al., 2017)

Author: Ali Mehdi
Date: January 12, 2026
"""

import numpy as np
from typing import Tuple, Optional, Union


class Dropout:
    """
    Standard Dropout implementation.
    
    Randomly sets a fraction of input units to 0 at each update during training,
    which helps prevent overfitting.
    
    Args:
        rate: Float between 0 and 1. Fraction of the input units to drop.
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropout = Dropout(rate=0.5)
        >>> x = np.random.randn(32, 128)
        >>> x_train = dropout(x, training=True)
        >>> x_test = dropout(x, training=False)
    
    Reference:
        Srivastava et al., "Dropout: A Simple Way to Prevent Neural Networks 
        from Overfitting", JMLR 2014
    """
    
    def __init__(self, rate: float = 0.5, seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        
        self.rate = rate
        self.seed = seed
        self._rng = np.random.RandomState(seed)
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Apply dropout to input.
        
        Args:
            x: Input array of any shape
            training: Whether in training mode (apply dropout) or inference mode
        
        Returns:
            Output array with dropout applied (if training=True)
        """
        if not training or self.rate == 0:
            return x
        
        # Generate binary mask
        keep_prob = 1 - self.rate
        mask = self._rng.binomial(1, keep_prob, size=x.shape)
        
        # Apply mask and scale
        return x * mask / keep_prob
    
    def get_mask(self, shape: Tuple[int, ...]) -> np.ndarray:
        """Generate dropout mask for given shape."""
        keep_prob = 1 - self.rate
        return self._rng.binomial(1, keep_prob, size=shape)


class SpatialDropout2D:
    """
    Spatial Dropout for 2D inputs (e.g., images).
    
    This version performs the same function as Dropout, however it drops
    entire 2D feature maps instead of individual elements. Useful for
    convolutional layers where adjacent pixels are highly correlated.
    
    Args:
        rate: Float between 0 and 1. Fraction of the feature maps to drop.
        data_format: 'channels_first' or 'channels_last'
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropout = SpatialDropout2D(rate=0.2)
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, height, width)
        >>> x_dropped = dropout(x, training=True)
    
    Reference:
        Tompson et al., "Efficient Object Localization Using Convolutional Networks", 
        ICCV 2015
    """
    
    def __init__(self, rate: float = 0.5, data_format: str = 'channels_first', 
                 seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        if data_format not in ['channels_first', 'channels_last']:
            raise ValueError(f"data_format must be 'channels_first' or 'channels_last'")
        
        self.rate = rate
        self.data_format = data_format
        self.seed = seed
        self._rng = np.random.RandomState(seed)
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Apply spatial dropout to input.
        
        Args:
            x: Input array of shape (batch, channels, height, width) for channels_first
               or (batch, height, width, channels) for channels_last
            training: Whether in training mode
        
        Returns:
            Output array with spatial dropout applied
        """
        if not training or self.rate == 0:
            return x
        
        if x.ndim != 4:
            raise ValueError(f"Expected 4D input, got shape {x.shape}")
        
        keep_prob = 1 - self.rate
        
        # Determine noise shape (drop entire feature maps)
        if self.data_format == 'channels_first':
            # (batch, channels, 1, 1)
            noise_shape = (x.shape[0], x.shape[1], 1, 1)
        else:
            # (batch, 1, 1, channels)
            noise_shape = (x.shape[0], 1, 1, x.shape[3])
        
        # Generate mask and broadcast
        mask = self._rng.binomial(1, keep_prob, size=noise_shape)
        mask = np.broadcast_to(mask, x.shape)
        
        return x * mask / keep_prob


class SpatialDropout3D:
    """
    Spatial Dropout for 3D inputs (e.g., 3D convolutions, video).
    
    Drops entire 3D feature maps instead of individual elements.
    
    Args:
        rate: Float between 0 and 1. Fraction of the feature maps to drop.
        data_format: 'channels_first' or 'channels_last'
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropout = SpatialDropout3D(rate=0.2)
        >>> x = np.random.randn(16, 32, 10, 28, 28)  # (batch, channels, depth, height, width)
        >>> x_dropped = dropout(x, training=True)
    """
    
    def __init__(self, rate: float = 0.5, data_format: str = 'channels_first',
                 seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        if data_format not in ['channels_first', 'channels_last']:
            raise ValueError(f"data_format must be 'channels_first' or 'channels_last'")
        
        self.rate = rate
        self.data_format = data_format
        self.seed = seed
        self._rng = np.random.RandomState(seed)
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """Apply spatial dropout to 3D input."""
        if not training or self.rate == 0:
            return x
        
        if x.ndim != 5:
            raise ValueError(f"Expected 5D input, got shape {x.shape}")
        
        keep_prob = 1 - self.rate
        
        # Determine noise shape
        if self.data_format == 'channels_first':
            # (batch, channels, 1, 1, 1)
            noise_shape = (x.shape[0], x.shape[1], 1, 1, 1)
        else:
            # (batch, 1, 1, 1, channels)
            noise_shape = (x.shape[0], 1, 1, 1, x.shape[4])
        
        # Generate mask and broadcast
        mask = self._rng.binomial(1, keep_prob, size=noise_shape)
        mask = np.broadcast_to(mask, x.shape)
        
        return x * mask / keep_prob


class VariationalDropout:
    """
    Variational Dropout for RNNs.
    
    Uses the same dropout mask across all time steps, which is more effective
    for recurrent networks than applying different masks at each time step.
    
    Args:
        rate: Float between 0 and 1. Fraction of the input units to drop.
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropout = VariationalDropout(rate=0.3)
        >>> x = np.random.randn(32, 10, 128)  # (batch, time_steps, features)
        >>> x_dropped = dropout(x, training=True)
    
    Reference:
        Gal & Ghahramani, "A Theoretically Grounded Application of Dropout in 
        Recurrent Neural Networks", NIPS 2016
    """
    
    def __init__(self, rate: float = 0.5, seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        
        self.rate = rate
        self.seed = seed
        self._rng = np.random.RandomState(seed)
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Apply variational dropout to input.
        
        Args:
            x: Input array of shape (batch, time_steps, features)
            training: Whether in training mode
        
        Returns:
            Output array with same dropout mask across time steps
        """
        if not training or self.rate == 0:
            return x
        
        if x.ndim != 3:
            raise ValueError(f"Expected 3D input (batch, time, features), got shape {x.shape}")
        
        keep_prob = 1 - self.rate
        
        # Generate mask for (batch, 1, features) and broadcast across time
        noise_shape = (x.shape[0], 1, x.shape[2])
        mask = self._rng.binomial(1, keep_prob, size=noise_shape)
        mask = np.broadcast_to(mask, x.shape)
        
        return x * mask / keep_prob


class DropConnect:
    """
    DropConnect implementation.
    
    Instead of dropping neuron activations, DropConnect drops connections (weights)
    between neurons. This provides stronger regularization than standard dropout.
    
    Args:
        rate: Float between 0 and 1. Fraction of connections to drop.
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropconnect = DropConnect(rate=0.5)
        >>> x = np.random.randn(32, 128)
        >>> W = np.random.randn(128, 64)
        >>> output = dropconnect.apply(x, W, training=True)
    
    Reference:
        Wan et al., "Regularization of Neural Networks using DropConnect", ICML 2013
    """
    
    def __init__(self, rate: float = 0.5, seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        
        self.rate = rate
        self.seed = seed
        self._rng = np.random.RandomState(seed)
    
    def apply(self, x: np.ndarray, weights: np.ndarray, 
              training: bool = True) -> np.ndarray:
        """
        Apply DropConnect to weight matrix.
        
        Args:
            x: Input array of shape (batch, input_dim)
            weights: Weight matrix of shape (input_dim, output_dim)
            training: Whether in training mode
        
        Returns:
            Output array of shape (batch, output_dim)
        """
        if not training or self.rate == 0:
            return np.dot(x, weights)
        
        keep_prob = 1 - self.rate
        
        # Drop connections (weights)
        mask = self._rng.binomial(1, keep_prob, size=weights.shape)
        masked_weights = weights * mask / keep_prob
        
        return np.dot(x, masked_weights)
    
    def get_mask(self, shape: Tuple[int, ...]) -> np.ndarray:
        """Generate DropConnect mask for given weight shape."""
        keep_prob = 1 - self.rate
        return self._rng.binomial(1, keep_prob, size=shape)


class AlphaDropout:
    """
    Alpha Dropout for Self-Normalizing Neural Networks (SNNs).
    
    Alpha Dropout maintains the self-normalizing property of SNNs by ensuring
    that mean and variance are preserved. Works with SELU activation.
    
    Args:
        rate: Float between 0 and 1. Fraction of the input units to drop.
        seed: Random seed for reproducibility.
    
    Example:
        >>> dropout = AlphaDropout(rate=0.1)
        >>> x = np.random.randn(32, 128)
        >>> x_dropped = dropout(x, training=True)
    
    Reference:
        Klambauer et al., "Self-Normalizing Neural Networks", NIPS 2017
    """
    
    def __init__(self, rate: float = 0.5, seed: Optional[int] = None):
        if not 0 <= rate < 1:
            raise ValueError(f"Dropout rate must be in [0, 1), got {rate}")
        
        self.rate = rate
        self.seed = seed
        self._rng = np.random.RandomState(seed)
        
        # SELU parameters
        self.alpha = 1.6732632423543772848170429916717
        self.scale = 1.0507009873554804934193349852946
        
        # Alpha dropout parameters
        self.alpha_p = -self.alpha * self.scale
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Apply alpha dropout to input.
        
        Args:
            x: Input array of any shape
            training: Whether in training mode
        
        Returns:
            Output array with alpha dropout applied
        """
        if not training or self.rate == 0:
            return x
        
        keep_prob = 1 - self.rate
        
        # Calculate affine transformation parameters
        a = ((1 - self.rate) * (1 + self.rate * self.alpha_p ** 2)) ** -0.5
        b = -a * self.alpha_p * self.rate
        
        # Generate mask
        mask = self._rng.binomial(1, keep_prob, size=x.shape)
        
        # Apply alpha dropout
        x_dropped = np.where(mask, x, self.alpha_p)
        
        # Affine transformation to preserve mean and variance
        return a * x_dropped + b


# Convenience functions
def dropout(x: np.ndarray, rate: float = 0.5, training: bool = True, 
            seed: Optional[int] = None) -> np.ndarray:
    """
    Apply standard dropout to input.
    
    Args:
        x: Input array
        rate: Dropout rate (fraction to drop)
        training: Whether in training mode
        seed: Random seed
    
    Returns:
        Output with dropout applied
    
    Example:
        >>> x = np.random.randn(32, 128)
        >>> x_dropped = dropout(x, rate=0.5, training=True)
    """
    drop = Dropout(rate=rate, seed=seed)
    return drop(x, training=training)


def spatial_dropout_2d(x: np.ndarray, rate: float = 0.5, training: bool = True,
                       data_format: str = 'channels_first',
                       seed: Optional[int] = None) -> np.ndarray:
    """
    Apply spatial dropout to 2D input.
    
    Args:
        x: Input array of shape (batch, channels, height, width) or 
           (batch, height, width, channels)
        rate: Dropout rate
        training: Whether in training mode
        data_format: 'channels_first' or 'channels_last'
        seed: Random seed
    
    Returns:
        Output with spatial dropout applied
    
    Example:
        >>> x = np.random.randn(32, 64, 28, 28)
        >>> x_dropped = spatial_dropout_2d(x, rate=0.2, training=True)
    """
    drop = SpatialDropout2D(rate=rate, data_format=data_format, seed=seed)
    return drop(x, training=training)


def spatial_dropout_3d(x: np.ndarray, rate: float = 0.5, training: bool = True,
                       data_format: str = 'channels_first',
                       seed: Optional[int] = None) -> np.ndarray:
    """
    Apply spatial dropout to 3D input.
    
    Args:
        x: Input array of shape (batch, channels, depth, height, width) or
           (batch, depth, height, width, channels)
        rate: Dropout rate
        training: Whether in training mode
        data_format: 'channels_first' or 'channels_last'
        seed: Random seed
    
    Returns:
        Output with spatial dropout applied
    
    Example:
        >>> x = np.random.randn(16, 32, 10, 28, 28)
        >>> x_dropped = spatial_dropout_3d(x, rate=0.2, training=True)
    """
    drop = SpatialDropout3D(rate=rate, data_format=data_format, seed=seed)
    return drop(x, training=training)


def variational_dropout(x: np.ndarray, rate: float = 0.5, training: bool = True,
                       seed: Optional[int] = None) -> np.ndarray:
    """
    Apply variational dropout to sequential input.
    
    Args:
        x: Input array of shape (batch, time_steps, features)
        rate: Dropout rate
        training: Whether in training mode
        seed: Random seed
    
    Returns:
        Output with variational dropout applied
    
    Example:
        >>> x = np.random.randn(32, 10, 128)
        >>> x_dropped = variational_dropout(x, rate=0.3, training=True)
    """
    drop = VariationalDropout(rate=rate, seed=seed)
    return drop(x, training=training)


def dropconnect(x: np.ndarray, weights: np.ndarray, rate: float = 0.5,
                training: bool = True, seed: Optional[int] = None) -> np.ndarray:
    """
    Apply DropConnect to weight matrix.
    
    Args:
        x: Input array of shape (batch, input_dim)
        weights: Weight matrix of shape (input_dim, output_dim)
        rate: Dropout rate
        training: Whether in training mode
        seed: Random seed
    
    Returns:
        Output array of shape (batch, output_dim)
    
    Example:
        >>> x = np.random.randn(32, 128)
        >>> W = np.random.randn(128, 64)
        >>> output = dropconnect(x, W, rate=0.5, training=True)
    """
    drop = DropConnect(rate=rate, seed=seed)
    return drop.apply(x, weights, training=training)


def alpha_dropout(x: np.ndarray, rate: float = 0.5, training: bool = True,
                  seed: Optional[int] = None) -> np.ndarray:
    """
    Apply alpha dropout to input.
    
    Args:
        x: Input array
        rate: Dropout rate
        training: Whether in training mode
        seed: Random seed
    
    Returns:
        Output with alpha dropout applied
    
    Example:
        >>> x = np.random.randn(32, 128)
        >>> x_dropped = alpha_dropout(x, rate=0.1, training=True)
    """
    drop = AlphaDropout(rate=rate, seed=seed)
    return drop(x, training=training)


__all__ = [
    'Dropout',
    'SpatialDropout2D',
    'SpatialDropout3D',
    'VariationalDropout',
    'DropConnect',
    'AlphaDropout',
    'dropout',
    'spatial_dropout_2d',
    'spatial_dropout_3d',
    'variational_dropout',
    'dropconnect',
    'alpha_dropout',
]
