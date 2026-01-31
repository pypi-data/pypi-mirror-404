"""
Loss Functions Suite

This module implements various loss functions for training neural networks.
Loss functions measure the difference between predictions and targets, guiding
the optimization process.

Implemented Functions:
1. MSE (Mean Squared Error) - Regression
2. MAE (Mean Absolute Error) - Regression
3. Huber Loss - Robust Regression
4. Cross Entropy - Classification
5. Binary Cross Entropy - Binary Classification
6. Focal Loss - Imbalanced Classification
7. Dice Loss - Segmentation
8. Hinge Loss - SVM-style Classification
9. KL Divergence - Distribution Matching
10. Cosine Similarity Loss - Embedding Learning
11. Triplet Loss - Metric Learning

References:
- MSE/MAE: Classic regression losses
- Huber: "Robust Estimation of a Location Parameter" (Huber, 1964)
- Cross Entropy: Information theory foundation
- Focal Loss: "Focal Loss for Dense Object Detection" (Lin et al., 2017)
- Dice Loss: "V-Net: Fully Convolutional Neural Networks" (Milletari et al., 2016)
- Hinge Loss: Support Vector Machines
- KL Divergence: Kullback-Leibler divergence
- Triplet Loss: "FaceNet: A Unified Embedding" (Schroff et al., 2015)

Author: Ali Mehdi
Date: January 13, 2026
"""

import numpy as np
from typing import Optional, Tuple


class MSE:
    """
    Mean Squared Error Loss.
    
    Measures the average squared difference between predictions and targets.
    Sensitive to outliers due to squaring. Standard choice for regression.
    
    Formula: L = (1/n) * Σ(y_true - y_pred)²
    
    Args:
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> mse = MSE()
        >>> y_true = np.array([1.0, 2.0, 3.0])
        >>> y_pred = np.array([1.1, 2.2, 2.9])
        >>> loss = mse(y_true, y_pred)
        >>> print(f"MSE Loss: {loss:.4f}")
    
    Reference:
        Classic regression loss function
    """
    
    def __init__(self, reduction: str = 'mean'):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        self.reduction = reduction
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute MSE loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        squared_diff = (y_true - y_pred) ** 2
        
        if self.reduction == 'mean':
            return np.mean(squared_diff)
        elif self.reduction == 'sum':
            return np.sum(squared_diff)
        else:
            return squared_diff
    
    def gradient(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute gradient with respect to predictions."""
        n = y_true.size if self.reduction == 'mean' else 1
        return -2 * (y_true - y_pred) / n


class MAE:
    """
    Mean Absolute Error Loss.
    
    Measures the average absolute difference between predictions and targets.
    More robust to outliers than MSE. Linear penalty.
    
    Formula: L = (1/n) * Σ|y_true - y_pred|
    
    Args:
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> mae = MAE()
        >>> y_true = np.array([1.0, 2.0, 3.0])
        >>> y_pred = np.array([1.1, 2.2, 2.9])
        >>> loss = mae(y_true, y_pred)
        >>> print(f"MAE Loss: {loss:.4f}")
    
    Reference:
        Classic regression loss function
    """
    
    def __init__(self, reduction: str = 'mean'):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        self.reduction = reduction
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute MAE loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        abs_diff = np.abs(y_true - y_pred)
        
        if self.reduction == 'mean':
            return np.mean(abs_diff)
        elif self.reduction == 'sum':
            return np.sum(abs_diff)
        else:
            return abs_diff
    
    def gradient(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute gradient with respect to predictions."""
        n = y_true.size if self.reduction == 'mean' else 1
        return -np.sign(y_true - y_pred) / n


class HuberLoss:
    """
    Huber Loss.
    
    Combines MSE and MAE. Quadratic for small errors, linear for large errors.
    Robust to outliers while maintaining smoothness.
    
    Formula: 
        L = 0.5 * (y_true - y_pred)² if |y_true - y_pred| <= delta
        L = delta * (|y_true - y_pred| - 0.5 * delta) otherwise
    
    Args:
        delta: Threshold for switching between quadratic and linear (default: 1.0)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> huber = HuberLoss(delta=1.0)
        >>> y_true = np.array([1.0, 2.0, 3.0])
        >>> y_pred = np.array([1.1, 2.5, 2.9])
        >>> loss = huber(y_true, y_pred)
        >>> print(f"Huber Loss: {loss:.4f}")
    
    Reference:
        Huber, "Robust Estimation of a Location Parameter", 1964
    """
    
    def __init__(self, delta: float = 1.0, reduction: str = 'mean'):
        if delta <= 0:
            raise ValueError(f"delta must be positive, got {delta}")
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.delta = delta
        self.reduction = reduction
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute Huber loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        error = y_true - y_pred
        abs_error = np.abs(error)
        
        quadratic = 0.5 * error ** 2
        linear = self.delta * (abs_error - 0.5 * self.delta)
        
        loss = np.where(abs_error <= self.delta, quadratic, linear)
        
        if self.reduction == 'mean':
            return np.mean(loss)
        elif self.reduction == 'sum':
            return np.sum(loss)
        else:
            return loss
    
    def gradient(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute gradient with respect to predictions."""
        error = y_true - y_pred
        abs_error = np.abs(error)
        
        grad = np.where(abs_error <= self.delta, 
                       -error, 
                       -self.delta * np.sign(error))
        
        if self.reduction == 'mean':
            grad = grad / y_true.size
        
        return grad


class CrossEntropy:
    """
    Cross Entropy Loss.
    
    Standard loss for multi-class classification. Measures divergence between
    predicted probability distribution and true distribution.
    
    Formula: L = -Σ y_true * log(y_pred)
    
    Args:
        from_logits: If True, apply softmax to predictions (default: False)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
        epsilon: Small constant for numerical stability (default: 1e-7)
    
    Example:
        >>> ce = CrossEntropy()
        >>> y_true = np.array([[1, 0, 0], [0, 1, 0]])  # One-hot encoded
        >>> y_pred = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]])
        >>> loss = ce(y_true, y_pred)
        >>> print(f"Cross Entropy Loss: {loss:.4f}")
    
    Reference:
        Information theory foundation
    """
    
    def __init__(self, from_logits: bool = False, reduction: str = 'mean', 
                 epsilon: float = 1e-7):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.from_logits = from_logits
        self.reduction = reduction
        self.epsilon = epsilon
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute cross entropy loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        if self.from_logits:
            y_pred = self._softmax(y_pred)
        
        # Clip predictions for numerical stability
        y_pred = np.clip(y_pred, self.epsilon, 1 - self.epsilon)
        
        # Compute cross entropy
        ce = -np.sum(y_true * np.log(y_pred), axis=-1)
        
        if self.reduction == 'mean':
            return np.mean(ce)
        elif self.reduction == 'sum':
            return np.sum(ce)
        else:
            return ce
    
    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax."""
        x_shifted = x - np.max(x, axis=-1, keepdims=True)
        exp_x = np.exp(x_shifted)
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


class BinaryCrossEntropy:
    """
    Binary Cross Entropy Loss.
    
    Loss for binary classification. Special case of cross entropy for two classes.
    
    Formula: L = -[y_true * log(y_pred) + (1 - y_true) * log(1 - y_pred)]
    
    Args:
        from_logits: If True, apply sigmoid to predictions (default: False)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
        epsilon: Small constant for numerical stability (default: 1e-7)
    
    Example:
        >>> bce = BinaryCrossEntropy()
        >>> y_true = np.array([1, 0, 1, 0])
        >>> y_pred = np.array([0.9, 0.1, 0.8, 0.2])
        >>> loss = bce(y_true, y_pred)
        >>> print(f"Binary Cross Entropy Loss: {loss:.4f}")
    
    Reference:
        Binary classification standard
    """
    
    def __init__(self, from_logits: bool = False, reduction: str = 'mean',
                 epsilon: float = 1e-7):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.from_logits = from_logits
        self.reduction = reduction
        self.epsilon = epsilon
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute binary cross entropy loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        if self.from_logits:
            y_pred = self._sigmoid(y_pred)
        
        # Clip predictions for numerical stability
        y_pred = np.clip(y_pred, self.epsilon, 1 - self.epsilon)
        
        # Compute binary cross entropy
        bce = -(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        
        if self.reduction == 'mean':
            return np.mean(bce)
        elif self.reduction == 'sum':
            return np.sum(bce)
        else:
            return bce
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return np.where(x >= 0, 
                       1 / (1 + np.exp(-x)),
                       np.exp(x) / (1 + np.exp(x)))


class FocalLoss:
    """
    Focal Loss.
    
    Addresses class imbalance by down-weighting easy examples and focusing
    on hard examples. Used in object detection (RetinaNet).
    
    Formula: L = -α * (1 - p_t)^γ * log(p_t)
    where p_t = p if y=1 else 1-p
    
    Args:
        alpha: Weighting factor for class balance (default: 0.25)
        gamma: Focusing parameter (default: 2.0)
        from_logits: If True, apply sigmoid to predictions (default: False)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
        epsilon: Small constant for numerical stability (default: 1e-7)
    
    Example:
        >>> focal = FocalLoss(alpha=0.25, gamma=2.0)
        >>> y_true = np.array([1, 0, 1, 0])
        >>> y_pred = np.array([0.9, 0.1, 0.6, 0.3])
        >>> loss = focal(y_true, y_pred)
        >>> print(f"Focal Loss: {loss:.4f}")
    
    Reference:
        Lin et al., "Focal Loss for Dense Object Detection", 2017
    """
    
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0,
                 from_logits: bool = False, reduction: str = 'mean',
                 epsilon: float = 1e-7):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.alpha = alpha
        self.gamma = gamma
        self.from_logits = from_logits
        self.reduction = reduction
        self.epsilon = epsilon
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute focal loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        if self.from_logits:
            y_pred = self._sigmoid(y_pred)
        
        # Clip predictions for numerical stability
        y_pred = np.clip(y_pred, self.epsilon, 1 - self.epsilon)
        
        # Compute p_t
        p_t = np.where(y_true == 1, y_pred, 1 - y_pred)
        
        # Compute focal loss
        focal = -self.alpha * (1 - p_t) ** self.gamma * np.log(p_t)
        
        if self.reduction == 'mean':
            return np.mean(focal)
        elif self.reduction == 'sum':
            return np.sum(focal)
        else:
            return focal
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return np.where(x >= 0, 
                       1 / (1 + np.exp(-x)),
                       np.exp(x) / (1 + np.exp(x)))


class DiceLoss:
    """
    Dice Loss.
    
    Measures overlap between predicted and ground truth segmentation masks.
    Handles class imbalance well. Used in medical image segmentation.
    
    Formula: L = 1 - (2 * |X ∩ Y| + smooth) / (|X| + |Y| + smooth)
    
    Args:
        smooth: Smoothing constant to avoid division by zero (default: 1.0)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> dice = DiceLoss()
        >>> y_true = np.array([[1, 1, 0], [0, 1, 1]])
        >>> y_pred = np.array([[0.9, 0.8, 0.1], [0.2, 0.9, 0.8]])
        >>> loss = dice(y_true, y_pred)
        >>> print(f"Dice Loss: {loss:.4f}")
    
    Reference:
        Milletari et al., "V-Net: Fully Convolutional Neural Networks", 2016
    """
    
    def __init__(self, smooth: float = 1.0, reduction: str = 'mean'):
        if smooth < 0:
            raise ValueError(f"smooth must be non-negative, got {smooth}")
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.smooth = smooth
        self.reduction = reduction
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute Dice loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        # Flatten arrays
        y_true_flat = y_true.reshape(y_true.shape[0], -1)
        y_pred_flat = y_pred.reshape(y_pred.shape[0], -1)
        
        # Compute intersection and union
        intersection = np.sum(y_true_flat * y_pred_flat, axis=1)
        union = np.sum(y_true_flat, axis=1) + np.sum(y_pred_flat, axis=1)
        
        # Compute Dice coefficient
        dice_coef = (2.0 * intersection + self.smooth) / (union + self.smooth)
        
        # Dice loss = 1 - Dice coefficient
        dice_loss = 1.0 - dice_coef
        
        if self.reduction == 'mean':
            return np.mean(dice_loss)
        elif self.reduction == 'sum':
            return np.sum(dice_loss)
        else:
            return dice_loss


class HingeLoss:
    """
    Hinge Loss.
    
    SVM-style loss for binary classification. Encourages correct classification
    with a margin.
    
    Formula: L = max(0, 1 - y_true * y_pred)
    where y_true ∈ {-1, 1}
    
    Args:
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> hinge = HingeLoss()
        >>> y_true = np.array([1, -1, 1, -1])
        >>> y_pred = np.array([0.8, -0.9, 0.5, -0.6])
        >>> loss = hinge(y_true, y_pred)
        >>> print(f"Hinge Loss: {loss:.4f}")
    
    Reference:
        Support Vector Machines
    """
    
    def __init__(self, reduction: str = 'mean'):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        self.reduction = reduction
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute hinge loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        # Hinge loss
        hinge = np.maximum(0, 1 - y_true * y_pred)
        
        if self.reduction == 'mean':
            return np.mean(hinge)
        elif self.reduction == 'sum':
            return np.sum(hinge)
        else:
            return hinge


class KLDivergence:
    """
    Kullback-Leibler Divergence Loss.
    
    Measures how one probability distribution diverges from another.
    Used in knowledge distillation and variational inference.
    
    Formula: L = Σ y_true * log(y_true / y_pred)
    
    Args:
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
        epsilon: Small constant for numerical stability (default: 1e-7)
    
    Example:
        >>> kl = KLDivergence()
        >>> y_true = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]])
        >>> y_pred = np.array([[0.6, 0.3, 0.1], [0.2, 0.7, 0.1]])
        >>> loss = kl(y_true, y_pred)
        >>> print(f"KL Divergence: {loss:.4f}")
    
    Reference:
        Kullback-Leibler divergence
    """
    
    def __init__(self, reduction: str = 'mean', epsilon: float = 1e-7):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.reduction = reduction
        self.epsilon = epsilon
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute KL divergence."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        # Clip for numerical stability
        y_true = np.clip(y_true, self.epsilon, 1)
        y_pred = np.clip(y_pred, self.epsilon, 1)
        
        # Compute KL divergence
        kl = np.sum(y_true * np.log(y_true / y_pred), axis=-1)
        
        if self.reduction == 'mean':
            return np.mean(kl)
        elif self.reduction == 'sum':
            return np.sum(kl)
        else:
            return kl


class CosineSimilarityLoss:
    """
    Cosine Similarity Loss.
    
    Measures the cosine of the angle between two vectors. Used in embedding
    learning and similarity tasks.
    
    Formula: L = 1 - (A · B) / (||A|| * ||B||)
    
    Args:
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
        epsilon: Small constant for numerical stability (default: 1e-8)
    
    Example:
        >>> cosine = CosineSimilarityLoss()
        >>> y_true = np.array([[1, 2, 3], [4, 5, 6]])
        >>> y_pred = np.array([[1.1, 2.1, 2.9], [3.9, 5.1, 6.1]])
        >>> loss = cosine(y_true, y_pred)
        >>> print(f"Cosine Similarity Loss: {loss:.4f}")
    
    Reference:
        Embedding learning
    """
    
    def __init__(self, reduction: str = 'mean', epsilon: float = 1e-8):
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.reduction = reduction
        self.epsilon = epsilon
    
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute cosine similarity loss."""
        if y_true.shape != y_pred.shape:
            raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
        # Compute dot product
        dot_product = np.sum(y_true * y_pred, axis=-1)
        
        # Compute norms
        norm_true = np.sqrt(np.sum(y_true ** 2, axis=-1))
        norm_pred = np.sqrt(np.sum(y_pred ** 2, axis=-1))
        
        # Compute cosine similarity
        cosine_sim = dot_product / (norm_true * norm_pred + self.epsilon)
        
        # Cosine similarity loss = 1 - cosine similarity
        loss = 1 - cosine_sim
        
        if self.reduction == 'mean':
            return np.mean(loss)
        elif self.reduction == 'sum':
            return np.sum(loss)
        else:
            return loss


class TripletLoss:
    """
    Triplet Loss.
    
    Used in metric learning to learn embeddings where similar items are close
    and dissimilar items are far apart.
    
    Formula: L = max(0, ||anchor - positive||² - ||anchor - negative||² + margin)
    
    Args:
        margin: Minimum distance between positive and negative pairs (default: 1.0)
        reduction: 'mean', 'sum', or 'none' (default: 'mean')
    
    Example:
        >>> triplet = TripletLoss(margin=1.0)
        >>> anchor = np.array([[1, 2], [3, 4]])
        >>> positive = np.array([[1.1, 2.1], [3.1, 4.1]])
        >>> negative = np.array([[5, 6], [7, 8]])
        >>> loss = triplet(anchor, positive, negative)
        >>> print(f"Triplet Loss: {loss:.4f}")
    
    Reference:
        Schroff et al., "FaceNet: A Unified Embedding", 2015
    """
    
    def __init__(self, margin: float = 1.0, reduction: str = 'mean'):
        if margin < 0:
            raise ValueError(f"margin must be non-negative, got {margin}")
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"reduction must be 'mean', 'sum', or 'none', got {reduction}")
        
        self.margin = margin
        self.reduction = reduction
    
    def __call__(self, anchor: np.ndarray, positive: np.ndarray, 
                 negative: np.ndarray) -> np.ndarray:
        """Compute triplet loss."""
        if anchor.shape != positive.shape or anchor.shape != negative.shape:
            raise ValueError("All inputs must have the same shape")
        
        # Compute distances
        pos_dist = np.sum((anchor - positive) ** 2, axis=-1)
        neg_dist = np.sum((anchor - negative) ** 2, axis=-1)
        
        # Compute triplet loss
        loss = np.maximum(0, pos_dist - neg_dist + self.margin)
        
        if self.reduction == 'mean':
            return np.mean(loss)
        elif self.reduction == 'sum':
            return np.sum(loss)
        else:
            return loss


# Convenience functions
def mse_loss(y_true: np.ndarray, y_pred: np.ndarray, reduction: str = 'mean') -> np.ndarray:
    """Compute MSE loss."""
    return MSE(reduction=reduction)(y_true, y_pred)


def mae_loss(y_true: np.ndarray, y_pred: np.ndarray, reduction: str = 'mean') -> np.ndarray:
    """Compute MAE loss."""
    return MAE(reduction=reduction)(y_true, y_pred)


def huber_loss(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0,
               reduction: str = 'mean') -> np.ndarray:
    """Compute Huber loss."""
    return HuberLoss(delta=delta, reduction=reduction)(y_true, y_pred)


def cross_entropy_loss(y_true: np.ndarray, y_pred: np.ndarray, from_logits: bool = False,
                       reduction: str = 'mean') -> np.ndarray:
    """Compute cross entropy loss."""
    return CrossEntropy(from_logits=from_logits, reduction=reduction)(y_true, y_pred)


def binary_cross_entropy_loss(y_true: np.ndarray, y_pred: np.ndarray, from_logits: bool = False,
                               reduction: str = 'mean') -> np.ndarray:
    """Compute binary cross entropy loss."""
    return BinaryCrossEntropy(from_logits=from_logits, reduction=reduction)(y_true, y_pred)


def focal_loss(y_true: np.ndarray, y_pred: np.ndarray, alpha: float = 0.25, gamma: float = 2.0,
               from_logits: bool = False, reduction: str = 'mean') -> np.ndarray:
    """Compute focal loss."""
    return FocalLoss(alpha=alpha, gamma=gamma, from_logits=from_logits, 
                     reduction=reduction)(y_true, y_pred)


def dice_loss(y_true: np.ndarray, y_pred: np.ndarray, smooth: float = 1.0,
              reduction: str = 'mean') -> np.ndarray:
    """Compute Dice loss."""
    return DiceLoss(smooth=smooth, reduction=reduction)(y_true, y_pred)


def hinge_loss(y_true: np.ndarray, y_pred: np.ndarray, reduction: str = 'mean') -> np.ndarray:
    """Compute hinge loss."""
    return HingeLoss(reduction=reduction)(y_true, y_pred)


def kl_divergence_loss(y_true: np.ndarray, y_pred: np.ndarray, 
                       reduction: str = 'mean') -> np.ndarray:
    """Compute KL divergence loss."""
    return KLDivergence(reduction=reduction)(y_true, y_pred)


def cosine_similarity_loss(y_true: np.ndarray, y_pred: np.ndarray,
                           reduction: str = 'mean') -> np.ndarray:
    """Compute cosine similarity loss."""
    return CosineSimilarityLoss(reduction=reduction)(y_true, y_pred)


def triplet_loss(anchor: np.ndarray, positive: np.ndarray, negative: np.ndarray,
                 margin: float = 1.0, reduction: str = 'mean') -> np.ndarray:
    """Compute triplet loss."""
    return TripletLoss(margin=margin, reduction=reduction)(anchor, positive, negative)


__all__ = [
    'MSE',
    'MAE',
    'HuberLoss',
    'CrossEntropy',
    'BinaryCrossEntropy',
    'FocalLoss',
    'DiceLoss',
    'HingeLoss',
    'KLDivergence',
    'CosineSimilarityLoss',
    'TripletLoss',
    'mse_loss',
    'mae_loss',
    'huber_loss',
    'cross_entropy_loss',
    'binary_cross_entropy_loss',
    'focal_loss',
    'dice_loss',
    'hinge_loss',
    'kl_divergence_loss',
    'cosine_similarity_loss',
    'triplet_loss',
]
