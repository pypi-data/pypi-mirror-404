"""
Dropout and Regularization Techniques

This module provides regularization methods to prevent overfitting:
- Dropout (Standard, Spatial, Variational, DropConnect)
- L1 Regularization (Lasso)
- L2 Regularization (Ridge)
- Elastic Net (L1 + L2)
- Weight Decay
- Early Stopping utilities

All operations support batched inputs and are optimized for deep learning.
"""

import numpy as np
from typing import Tuple, Optional, Dict, List


# ============================================================================
# DROPOUT
# ============================================================================

def dropout(
    x: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Standard Dropout
    
    Randomly drops neurons during training to prevent overfitting.
    
    Formula (Inverted Dropout):
        Training: y = (mask * x) / (1 - p)
        Inference: y = x
    
    Args:
        x: Input tensor, any shape
        dropout_rate: Probability of dropping a neuron (0 to 1)
        training: Whether in training mode
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (output, mask)
        
    Example:
        >>> import numpy as np
        >>> from ilovetools.ml.regularization import dropout
        
        >>> x = np.random.randn(32, 128)
        >>> output, mask = dropout(x, dropout_rate=0.5, training=True)
        >>> print(output.shape)  # (32, 128)
        >>> print(f"Dropped {np.sum(mask == 0)} neurons")
        
        >>> # Inference mode
        >>> output, mask = dropout(x, dropout_rate=0.5, training=False)
        >>> print(np.array_equal(output, x))  # True
    """
    if not training or dropout_rate == 0.0:
        # No dropout during inference or if rate is 0
        return x, np.ones_like(x)
    
    if dropout_rate >= 1.0:
        raise ValueError("dropout_rate must be less than 1.0")
    
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    # Generate binary mask
    mask = np.random.binomial(1, 1 - dropout_rate, size=x.shape)
    
    # Apply inverted dropout (scale during training)
    output = (x * mask) / (1 - dropout_rate)
    
    return output, mask


def spatial_dropout(
    x: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Spatial Dropout (for CNNs)
    
    Drops entire feature maps instead of individual neurons.
    Better for convolutional layers.
    
    Args:
        x: Input tensor, shape (batch, channels, height, width)
        dropout_rate: Probability of dropping a channel
        training: Whether in training mode
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (output, mask)
        
    Example:
        >>> x = np.random.randn(32, 64, 28, 28)  # (batch, channels, H, W)
        >>> output, mask = spatial_dropout(x, dropout_rate=0.2, training=True)
        >>> print(output.shape)  # (32, 64, 28, 28)
    """
    if not training or dropout_rate == 0.0:
        return x, np.ones_like(x)
    
    if x.ndim != 4:
        raise ValueError("spatial_dropout requires 4D input (batch, channels, H, W)")
    
    if seed is not None:
        np.random.seed(seed)
    
    batch_size, channels, height, width = x.shape
    
    # Generate mask for channels only
    channel_mask = np.random.binomial(1, 1 - dropout_rate, size=(batch_size, channels, 1, 1))
    
    # Broadcast mask to full shape
    mask = np.broadcast_to(channel_mask, x.shape).copy()
    
    # Apply inverted dropout
    output = (x * mask) / (1 - dropout_rate)
    
    return output, mask


def variational_dropout(
    x: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Variational Dropout (for RNNs)
    
    Uses the same dropout mask across all time steps.
    Better for recurrent networks.
    
    Args:
        x: Input tensor, shape (batch, seq_len, features)
        dropout_rate: Probability of dropping a feature
        training: Whether in training mode
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (output, mask)
        
    Example:
        >>> x = np.random.randn(32, 10, 512)  # (batch, seq_len, features)
        >>> output, mask = variational_dropout(x, dropout_rate=0.3, training=True)
        >>> print(output.shape)  # (32, 10, 512)
    """
    if not training or dropout_rate == 0.0:
        return x, np.ones_like(x)
    
    if x.ndim != 3:
        raise ValueError("variational_dropout requires 3D input (batch, seq_len, features)")
    
    if seed is not None:
        np.random.seed(seed)
    
    batch_size, seq_len, features = x.shape
    
    # Generate mask for features only (shared across time)
    feature_mask = np.random.binomial(1, 1 - dropout_rate, size=(batch_size, 1, features))
    
    # Broadcast mask to full shape
    mask = np.broadcast_to(feature_mask, x.shape).copy()
    
    # Apply inverted dropout
    output = (x * mask) / (1 - dropout_rate)
    
    return output, mask


def dropconnect(
    x: np.ndarray,
    weights: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    DropConnect
    
    Drops connections (weights) instead of neurons.
    
    Args:
        x: Input tensor, shape (batch, in_features)
        weights: Weight matrix, shape (out_features, in_features)
        dropout_rate: Probability of dropping a connection
        training: Whether in training mode
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (output, weight_mask)
        
    Example:
        >>> x = np.random.randn(32, 128)
        >>> weights = np.random.randn(256, 128)
        >>> output, mask = dropconnect(x, weights, dropout_rate=0.5, training=True)
        >>> print(output.shape)  # (32, 256)
    """
    if not training or dropout_rate == 0.0:
        return np.dot(x, weights.T), np.ones_like(weights)
    
    if seed is not None:
        np.random.seed(seed)
    
    # Generate mask for weights
    mask = np.random.binomial(1, 1 - dropout_rate, size=weights.shape)
    
    # Apply mask to weights
    masked_weights = (weights * mask) / (1 - dropout_rate)
    
    # Compute output
    output = np.dot(x, masked_weights.T)
    
    return output, mask


# ============================================================================
# L1 REGULARIZATION (LASSO)
# ============================================================================

def l1_regularization(
    weights: np.ndarray,
    lambda_: float = 0.01
) -> float:
    """
    L1 Regularization (Lasso)
    
    Adds absolute value penalty to loss.
    Encourages sparsity (many weights become zero).
    
    Formula:
        L1 = λ Σ|w_i|
    
    Args:
        weights: Weight tensor
        lambda_: Regularization strength
        
    Returns:
        L1 penalty value
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> penalty = l1_regularization(weights, lambda_=0.01)
        >>> print(f"L1 penalty: {penalty:.4f}")
    """
    return lambda_ * np.sum(np.abs(weights))


def l1_gradient(
    weights: np.ndarray,
    lambda_: float = 0.01
) -> np.ndarray:
    """
    Gradient of L1 regularization
    
    Formula:
        ∂L1/∂w = λ × sign(w)
    
    Args:
        weights: Weight tensor
        lambda_: Regularization strength
        
    Returns:
        Gradient of L1 penalty
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> grad = l1_gradient(weights, lambda_=0.01)
        >>> print(grad.shape)  # (256, 128)
    """
    return lambda_ * np.sign(weights)


# Alias for backward compatibility
l1_penalty = l1_gradient


# ============================================================================
# L2 REGULARIZATION (RIDGE)
# ============================================================================

def l2_regularization(
    weights: np.ndarray,
    lambda_: float = 0.01
) -> float:
    """
    L2 Regularization (Ridge / Weight Decay)
    
    Adds squared penalty to loss.
    Prevents large weights, encourages smooth distribution.
    
    Formula:
        L2 = λ Σw_i²
    
    Args:
        weights: Weight tensor
        lambda_: Regularization strength
        
    Returns:
        L2 penalty value
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> penalty = l2_regularization(weights, lambda_=0.01)
        >>> print(f"L2 penalty: {penalty:.4f}")
    """
    return lambda_ * np.sum(weights ** 2)


def l2_gradient(
    weights: np.ndarray,
    lambda_: float = 0.01
) -> np.ndarray:
    """
    Gradient of L2 regularization
    
    Formula:
        ∂L2/∂w = 2λw
    
    Args:
        weights: Weight tensor
        lambda_: Regularization strength
        
    Returns:
        Gradient of L2 penalty
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> grad = l2_gradient(weights, lambda_=0.01)
        >>> print(grad.shape)  # (256, 128)
    """
    return 2 * lambda_ * weights


# Alias for backward compatibility
l2_penalty = l2_gradient


def weight_decay(
    weights: np.ndarray,
    learning_rate: float,
    decay_rate: float = 0.01
) -> np.ndarray:
    """
    Weight Decay (equivalent to L2 regularization)
    
    Directly decays weights during optimization.
    
    Formula:
        w_new = w - lr × decay × w
              = w × (1 - lr × decay)
    
    Args:
        weights: Weight tensor
        learning_rate: Learning rate
        decay_rate: Decay rate (equivalent to λ in L2)
        
    Returns:
        Decayed weights
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> weights_new = weight_decay(weights, learning_rate=0.01, decay_rate=0.01)
        >>> print(weights_new.shape)  # (256, 128)
    """
    return weights * (1 - learning_rate * decay_rate)


# Alias
apply_weight_decay = weight_decay


# ============================================================================
# ELASTIC NET (L1 + L2)
# ============================================================================

def elastic_net_regularization(
    weights: np.ndarray,
    lambda_: float = 0.01,
    alpha: float = 0.5
) -> float:
    """
    Elastic Net Regularization (L1 + L2)
    
    Combines L1 and L2 penalties.
    
    Formula:
        ElasticNet = α × L1 + (1-α) × L2
                   = α × λ Σ|w_i| + (1-α) × λ Σw_i²
    
    Args:
        weights: Weight tensor
        lambda_: Overall regularization strength
        alpha: Balance between L1 and L2 (0 to 1)
               alpha=1: pure L1
               alpha=0: pure L2
               alpha=0.5: equal mix
        
    Returns:
        Elastic net penalty value
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> penalty = elastic_net_regularization(weights, lambda_=0.01, alpha=0.5)
        >>> print(f"Elastic net penalty: {penalty:.4f}")
    """
    l1_term = alpha * l1_regularization(weights, lambda_)
    l2_term = (1 - alpha) * l2_regularization(weights, lambda_)
    return l1_term + l2_term


def elastic_net_gradient(
    weights: np.ndarray,
    lambda_: float = 0.01,
    alpha: float = 0.5
) -> np.ndarray:
    """
    Gradient of Elastic Net regularization
    
    Formula:
        ∂ElasticNet/∂w = α × λ × sign(w) + (1-α) × 2λw
    
    Args:
        weights: Weight tensor
        lambda_: Overall regularization strength
        alpha: Balance between L1 and L2
        
    Returns:
        Gradient of elastic net penalty
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> grad = elastic_net_gradient(weights, lambda_=0.01, alpha=0.5)
        >>> print(grad.shape)  # (256, 128)
    """
    l1_grad = alpha * l1_gradient(weights, lambda_)
    l2_grad = (1 - alpha) * l2_gradient(weights, lambda_)
    return l1_grad + l2_grad


# Alias
elastic_net_penalty = elastic_net_gradient


# ============================================================================
# EARLY STOPPING
# ============================================================================

class EarlyStopping:
    """
    Early Stopping utility
    
    Stops training when validation loss stops improving.
    
    Example:
        >>> from ilovetools.ml.regularization import EarlyStopping
        
        >>> early_stopping = EarlyStopping(patience=10, min_delta=0.001)
        
        >>> for epoch in range(100):
        ...     train_loss = train_one_epoch()
        ...     val_loss = validate()
        ...     
        ...     if early_stopping(val_loss):
        ...         print(f"Early stopping at epoch {epoch}")
        ...         break
        ...     
        ...     if early_stopping.should_save():
        ...         save_model()
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.0,
        mode: str = 'min'
    ):
        """
        Initialize Early Stopping
        
        Args:
            patience: Number of epochs to wait before stopping
            min_delta: Minimum change to qualify as improvement
            mode: 'min' for loss, 'max' for accuracy
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.save_checkpoint = False
        
        if mode == 'min':
            self.best_score = np.inf
            self.is_better = lambda new, best: new < best - min_delta
        else:
            self.best_score = -np.inf
            self.is_better = lambda new, best: new > best + min_delta
    
    def __call__(self, score: float) -> bool:
        """
        Check if should stop training
        
        Args:
            score: Current validation score
            
        Returns:
            True if should stop, False otherwise
        """
        self.save_checkpoint = False
        
        if self.is_better(score, self.best_score):
            # Improvement
            self.best_score = score
            self.counter = 0
            self.save_checkpoint = True
        else:
            # No improvement
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        
        return self.early_stop
    
    def should_save(self) -> bool:
        """Check if should save checkpoint"""
        return self.save_checkpoint
    
    def reset(self):
        """Reset early stopping state"""
        self.counter = 0
        self.early_stop = False
        self.save_checkpoint = False
        if self.mode == 'min':
            self.best_score = np.inf
        else:
            self.best_score = -np.inf


# Utility functions for early stopping
def early_stopping_monitor(
    val_losses: List[float],
    patience: int = 10,
    min_delta: float = 0.0
) -> bool:
    """
    Simple early stopping monitor
    
    Args:
        val_losses: List of validation losses
        patience: Number of epochs to wait
        min_delta: Minimum improvement
        
    Returns:
        True if should stop
    """
    if len(val_losses) < patience + 1:
        return False
    
    best_loss = min(val_losses[:-patience])
    recent_best = min(val_losses[-patience:])
    
    return recent_best >= best_loss - min_delta


def should_stop_early(
    val_losses: List[float],
    patience: int = 10
) -> bool:
    """Alias for early_stopping_monitor"""
    return early_stopping_monitor(val_losses, patience)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def apply_regularization(
    weights: np.ndarray,
    reg_type: str = 'l2',
    lambda_: float = 0.01,
    alpha: float = 0.5
) -> float:
    """
    Apply regularization by type
    
    Args:
        weights: Weight tensor
        reg_type: Type of regularization ('l1', 'l2', 'elastic_net')
        lambda_: Regularization strength
        alpha: Balance for elastic net
        
    Returns:
        Regularization penalty
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> penalty = apply_regularization(weights, reg_type='l2', lambda_=0.01)
    """
    if reg_type == 'l1':
        return l1_regularization(weights, lambda_)
    elif reg_type == 'l2':
        return l2_regularization(weights, lambda_)
    elif reg_type == 'elastic_net':
        return elastic_net_regularization(weights, lambda_, alpha)
    else:
        raise ValueError(f"Unknown regularization type: {reg_type}")


def compute_regularization_loss(
    weights: np.ndarray,
    reg_type: str = 'l2',
    lambda_: float = 0.01,
    alpha: float = 0.5
) -> float:
    """Alias for apply_regularization"""
    return apply_regularization(weights, reg_type, lambda_, alpha)


def compute_regularization_gradient(
    weights: np.ndarray,
    reg_type: str = 'l2',
    lambda_: float = 0.01,
    alpha: float = 0.5
) -> np.ndarray:
    """
    Compute regularization gradient by type
    
    Args:
        weights: Weight tensor
        reg_type: Type of regularization ('l1', 'l2', 'elastic_net')
        lambda_: Regularization strength
        alpha: Balance for elastic net
        
    Returns:
        Regularization gradient
        
    Example:
        >>> weights = np.random.randn(256, 128)
        >>> grad = compute_regularization_gradient(weights, reg_type='l2')
    """
    if reg_type == 'l1':
        return l1_gradient(weights, lambda_)
    elif reg_type == 'l2':
        return l2_gradient(weights, lambda_)
    elif reg_type == 'elastic_net':
        return elastic_net_gradient(weights, lambda_, alpha)
    else:
        raise ValueError(f"Unknown regularization type: {reg_type}")


def get_dropout_rate_schedule(
    initial_rate: float = 0.5,
    final_rate: float = 0.1,
    num_epochs: int = 100,
    schedule_type: str = 'linear'
) -> np.ndarray:
    """
    Generate dropout rate schedule
    
    Args:
        initial_rate: Starting dropout rate
        final_rate: Ending dropout rate
        num_epochs: Number of epochs
        schedule_type: 'linear', 'exponential', or 'cosine'
        
    Returns:
        Array of dropout rates for each epoch
        
    Example:
        >>> rates = get_dropout_rate_schedule(0.5, 0.1, 100, 'linear')
        >>> print(rates[:5])  # First 5 epochs
    """
    if schedule_type == 'linear':
        return np.linspace(initial_rate, final_rate, num_epochs)
    elif schedule_type == 'exponential':
        decay = (final_rate / initial_rate) ** (1 / num_epochs)
        return initial_rate * (decay ** np.arange(num_epochs))
    elif schedule_type == 'cosine':
        return final_rate + 0.5 * (initial_rate - final_rate) * \
               (1 + np.cos(np.pi * np.arange(num_epochs) / num_epochs))
    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")


# Weight constraints (for backward compatibility)
def max_norm_constraint(weights: np.ndarray, max_value: float = 3.0) -> np.ndarray:
    """Constrain weights to maximum norm"""
    norm = np.linalg.norm(weights)
    if norm > max_value:
        return weights * (max_value / norm)
    return weights


def unit_norm_constraint(weights: np.ndarray) -> np.ndarray:
    """Constrain weights to unit norm"""
    return weights / (np.linalg.norm(weights) + 1e-8)


def non_negative_constraint(weights: np.ndarray) -> np.ndarray:
    """Constrain weights to be non-negative"""
    return np.maximum(weights, 0)


# Aliases for inverted dropout
inverted_dropout = dropout
dropout_mask = dropout
