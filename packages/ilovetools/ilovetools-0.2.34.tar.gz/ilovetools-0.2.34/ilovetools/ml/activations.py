"""
Activation Functions for Neural Networks
Comprehensive implementation of activation functions and their derivatives
"""

import numpy as np
from typing import Optional

__all__ = [
    # Basic Activations
    'sigmoid_activation',
    'tanh_activation',
    'relu_activation',
    'leaky_relu_activation',
    'elu_activation',
    'selu_activation',
    'gelu_activation',
    'swish_activation',
    'mish_activation',
    'softplus_activation',
    'softsign_activation',
    'hard_sigmoid_activation',
    'hard_tanh_activation',
    'softmax_activation',
    'log_softmax_activation',
    
    # Derivatives
    'sigmoid_derivative',
    'tanh_derivative',
    'relu_derivative',
    'leaky_relu_derivative',
    'elu_derivative',
    'swish_derivative',
    'softplus_derivative',
    
    # Utilities
    'apply_activation',
    'get_activation_function',
    
    # Convenient aliases (without _activation suffix)
    'sigmoid',
    'tanh',
    'relu',
    'leaky_relu',
    'elu',
    'selu',
    'gelu',
    'swish',
    'mish',
    'softplus',
    'softsign',
    'hard_sigmoid',
    'hard_tanh',
    'softmax',
    'log_softmax',
]


# ==================== BASIC ACTIVATIONS ====================

def sigmoid_activation(x: np.ndarray) -> np.ndarray:
    """
    Sigmoid activation function.
    
    σ(x) = 1 / (1 + e^(-x))
    
    Output range: (0, 1)
    
    Properties:
    - Smooth gradient
    - Good for binary classification
    - Suffers from vanishing gradient
    - Not zero-centered
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import sigmoid_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = sigmoid_activation(x)
        >>> print(output)
        [0.1192 0.2689 0.5000 0.7311 0.8808]
    """
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def tanh_activation(x: np.ndarray) -> np.ndarray:
    """
    Hyperbolic tangent activation function.
    
    tanh(x) = (e^x - e^(-x)) / (e^x + e^(-x))
    
    Output range: (-1, 1)
    
    Properties:
    - Zero-centered
    - Stronger gradients than sigmoid
    - Still suffers from vanishing gradient
    - Good for RNNs
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import tanh_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = tanh_activation(x)
        >>> print(output)
        [-0.9640 -0.7616  0.0000  0.7616  0.9640]
    """
    return np.tanh(x)


def relu_activation(x: np.ndarray) -> np.ndarray:
    """
    Rectified Linear Unit (ReLU) activation.
    
    ReLU(x) = max(0, x)
    
    Output range: [0, ∞)
    
    Properties:
    - Simple and fast
    - No vanishing gradient for positive values
    - Sparse activation
    - Can suffer from dying ReLU problem
    - Most popular for hidden layers
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import relu_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = relu_activation(x)
        >>> print(output)
        [0 0 0 1 2]
    """
    return np.maximum(0, x)


def leaky_relu_activation(
    x: np.ndarray,
    alpha: float = 0.01
) -> np.ndarray:
    """
    Leaky ReLU activation function.
    
    LeakyReLU(x) = max(αx, x)
    
    Output range: (-∞, ∞)
    
    Properties:
    - Fixes dying ReLU problem
    - Small negative slope for negative values
    - Fast computation
    - Good alternative to ReLU
    
    Args:
        x: Input array
        alpha: Slope for negative values (default: 0.01)
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import leaky_relu_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = leaky_relu_activation(x, alpha=0.01)
        >>> print(output)
        [-0.02 -0.01  0.00  1.00  2.00]
    """
    return np.where(x > 0, x, alpha * x)


def elu_activation(
    x: np.ndarray,
    alpha: float = 1.0
) -> np.ndarray:
    """
    Exponential Linear Unit (ELU) activation.
    
    ELU(x) = x if x > 0 else α(e^x - 1)
    
    Output range: (-α, ∞)
    
    Properties:
    - Smooth everywhere
    - Negative values push mean closer to zero
    - Self-normalizing properties
    - Slower than ReLU due to exponential
    - Good for deep networks
    
    Args:
        x: Input array
        alpha: Scale for negative values (default: 1.0)
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import elu_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = elu_activation(x, alpha=1.0)
        >>> print(output)
        [-0.8647 -0.6321  0.0000  1.0000  2.0000]
    """
    return np.where(x > 0, x, alpha * (np.exp(x) - 1))


def selu_activation(x: np.ndarray) -> np.ndarray:
    """
    Scaled Exponential Linear Unit (SELU) activation.
    
    SELU(x) = λ × ELU(x, α)
    
    where λ ≈ 1.0507 and α ≈ 1.6733
    
    Properties:
    - Self-normalizing
    - No batch normalization needed
    - Maintains mean 0 and variance 1
    - Good for deep feedforward networks
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import selu_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = selu_activation(x)
        >>> print(output)
        [-1.5202 -1.1113  0.0000  1.0507  2.1014]
    """
    alpha = 1.6732632423543772848170429916717
    scale = 1.0507009873554804934193349852946
    return scale * np.where(x > 0, x, alpha * (np.exp(x) - 1))


def gelu_activation(x: np.ndarray) -> np.ndarray:
    """
    Gaussian Error Linear Unit (GELU) activation.
    
    GELU(x) = x × Φ(x)
    where Φ(x) is the cumulative distribution function of the standard normal distribution
    
    Approximation: GELU(x) ≈ 0.5x(1 + tanh[√(2/π)(x + 0.044715x³)])
    
    Properties:
    - Smooth, non-monotonic
    - Used in BERT, GPT
    - Better than ReLU for Transformers
    - Stochastic regularizer
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import gelu_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = gelu_activation(x)
        >>> print(output)
        [-0.0454 -0.1588  0.0000  0.8412  1.9546]
    """
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))


def swish_activation(
    x: np.ndarray,
    beta: float = 1.0
) -> np.ndarray:
    """
    Swish activation function (also known as SiLU).
    
    Swish(x) = x × σ(βx)
    
    Properties:
    - Smooth, non-monotonic
    - Self-gated
    - Better than ReLU in deep networks
    - Used in EfficientNet
    
    Args:
        x: Input array
        beta: Scaling parameter (default: 1.0)
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import swish_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = swish_activation(x)
        >>> print(output)
        [-0.2384 -0.2689  0.0000  0.7311  1.7616]
    """
    return x * sigmoid_activation(beta * x)


def mish_activation(x: np.ndarray) -> np.ndarray:
    """
    Mish activation function.
    
    Mish(x) = x × tanh(softplus(x))
    
    Properties:
    - Smooth, non-monotonic
    - Self-regularizing
    - Better than ReLU and Swish in some cases
    - Unbounded above, bounded below
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import mish_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = mish_activation(x)
        >>> print(output)
        [-0.2525 -0.3034  0.0000  0.8651  1.9440]
    """
    return x * np.tanh(np.log(1 + np.exp(x)))


def softplus_activation(x: np.ndarray) -> np.ndarray:
    """
    Softplus activation function.
    
    Softplus(x) = log(1 + e^x)
    
    Properties:
    - Smooth approximation of ReLU
    - Always positive
    - Differentiable everywhere
    - Can be used as smooth ReLU
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import softplus_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = softplus_activation(x)
        >>> print(output)
        [0.1269 0.3133 0.6931 1.3133 2.1269]
    """
    return np.log(1 + np.exp(np.clip(x, -500, 500)))


def softsign_activation(x: np.ndarray) -> np.ndarray:
    """
    Softsign activation function.
    
    Softsign(x) = x / (1 + |x|)
    
    Output range: (-1, 1)
    
    Properties:
    - Similar to tanh but polynomial
    - Faster than tanh
    - Smoother than ReLU
    - Bounded output
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import softsign_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = softsign_activation(x)
        >>> print(output)
        [-0.6667 -0.5000  0.0000  0.5000  0.6667]
    """
    return x / (1 + np.abs(x))


def hard_sigmoid_activation(x: np.ndarray) -> np.ndarray:
    """
    Hard sigmoid activation function.
    
    HardSigmoid(x) = clip((x + 1) / 2, 0, 1)
    
    Output range: [0, 1]
    
    Properties:
    - Piecewise linear approximation of sigmoid
    - Faster than sigmoid
    - Used in mobile/embedded systems
    - Good for quantization
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import hard_sigmoid_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = hard_sigmoid_activation(x)
        >>> print(output)
        [0.0000 0.0000 0.5000 1.0000 1.0000]
    """
    return np.clip((x + 1) / 2, 0, 1)


def hard_tanh_activation(x: np.ndarray) -> np.ndarray:
    """
    Hard tanh activation function.
    
    HardTanh(x) = clip(x, -1, 1)
    
    Output range: [-1, 1]
    
    Properties:
    - Piecewise linear approximation of tanh
    - Faster than tanh
    - Used in mobile/embedded systems
    - Good for quantization
    
    Args:
        x: Input array
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import hard_tanh_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = hard_tanh_activation(x)
        >>> print(output)
        [-1 -1  0  1  1]
    """
    return np.clip(x, -1, 1)


def softmax_activation(
    x: np.ndarray,
    axis: int = -1
) -> np.ndarray:
    """
    Softmax activation function.
    
    Softmax(x_i) = e^(x_i) / Σ e^(x_j)
    
    Properties:
    - Converts logits to probabilities
    - Output sums to 1
    - Used for multi-class classification
    - Differentiable
    
    Args:
        x: Input array
        axis: Axis along which to compute softmax
    
    Returns:
        Probability distribution
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import softmax_activation
        
        >>> x = np.array([1, 2, 3, 4, 5])
        >>> output = softmax_activation(x)
        >>> print(output)
        [0.0117 0.0317 0.0861 0.2341 0.6364]
        >>> print(np.sum(output))  # Should be 1.0
        1.0
    """
    # Subtract max for numerical stability
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def log_softmax_activation(
    x: np.ndarray,
    axis: int = -1
) -> np.ndarray:
    """
    Log-softmax activation function.
    
    LogSoftmax(x_i) = log(e^(x_i) / Σ e^(x_j))
                    = x_i - log(Σ e^(x_j))
    
    Properties:
    - Numerically stable version of log(softmax(x))
    - Used with negative log-likelihood loss
    - Better numerical properties than log(softmax(x))
    
    Args:
        x: Input array
        axis: Axis along which to compute log-softmax
    
    Returns:
        Log probabilities
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import log_softmax_activation
        
        >>> x = np.array([1, 2, 3, 4, 5])
        >>> output = log_softmax_activation(x)
        >>> print(output)
        [-4.4519 -3.4519 -2.4519 -1.4519 -0.4519]
    """
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    return x_shifted - np.log(np.sum(np.exp(x_shifted), axis=axis, keepdims=True))


# ==================== DERIVATIVES ====================

def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of sigmoid activation.
    
    σ'(x) = σ(x) × (1 - σ(x))
    
    Args:
        x: Input array (can be pre-activated or post-activated)
    
    Returns:
        Derivative
    """
    s = sigmoid_activation(x)
    return s * (1 - s)


def tanh_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of tanh activation.
    
    tanh'(x) = 1 - tanh²(x)
    
    Args:
        x: Input array
    
    Returns:
        Derivative
    """
    t = tanh_activation(x)
    return 1 - t**2


def relu_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of ReLU activation.
    
    ReLU'(x) = 1 if x > 0 else 0
    
    Args:
        x: Input array
    
    Returns:
        Derivative
    """
    return np.where(x > 0, 1, 0)


def leaky_relu_derivative(
    x: np.ndarray,
    alpha: float = 0.01
) -> np.ndarray:
    """
    Derivative of Leaky ReLU activation.
    
    LeakyReLU'(x) = 1 if x > 0 else α
    
    Args:
        x: Input array
        alpha: Slope for negative values
    
    Returns:
        Derivative
    """
    return np.where(x > 0, 1, alpha)


def elu_derivative(
    x: np.ndarray,
    alpha: float = 1.0
) -> np.ndarray:
    """
    Derivative of ELU activation.
    
    ELU'(x) = 1 if x > 0 else α × e^x
    
    Args:
        x: Input array
        alpha: Scale for negative values
    
    Returns:
        Derivative
    """
    return np.where(x > 0, 1, alpha * np.exp(x))


def swish_derivative(
    x: np.ndarray,
    beta: float = 1.0
) -> np.ndarray:
    """
    Derivative of Swish activation.
    
    Swish'(x) = Swish(x) + σ(βx) × (1 - Swish(x))
    
    Args:
        x: Input array
        beta: Scaling parameter
    
    Returns:
        Derivative
    """
    swish = swish_activation(x, beta)
    sigmoid = sigmoid_activation(beta * x)
    return swish + sigmoid * (1 - swish)


def softplus_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of Softplus activation.
    
    Softplus'(x) = σ(x)
    
    Args:
        x: Input array
    
    Returns:
        Derivative
    """
    return sigmoid_activation(x)


# ==================== UTILITIES ====================

def apply_activation(
    x: np.ndarray,
    activation: str,
    **kwargs
) -> np.ndarray:
    """
    Apply activation function by name.
    
    Args:
        x: Input array
        activation: Name of activation function
        **kwargs: Additional arguments for activation function
    
    Returns:
        Activated output
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import apply_activation
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = apply_activation(x, 'relu')
        >>> print(output)
        [0 0 0 1 2]
    """
    activation_func = get_activation_function(activation)
    return activation_func(x, **kwargs)


def get_activation_function(activation: str):
    """
    Get activation function by name.
    
    Args:
        activation: Name of activation function
    
    Returns:
        Activation function
    
    Examples:
        >>> from ilovetools.ml import get_activation_function
        
        >>> relu_func = get_activation_function('relu')
        >>> print(relu_func.__name__)
        relu_activation
    """
    activation_map = {
        'sigmoid': sigmoid_activation,
        'tanh': tanh_activation,
        'relu': relu_activation,
        'leaky_relu': leaky_relu_activation,
        'elu': elu_activation,
        'selu': selu_activation,
        'gelu': gelu_activation,
        'swish': swish_activation,
        'mish': mish_activation,
        'softplus': softplus_activation,
        'softsign': softsign_activation,
        'hard_sigmoid': hard_sigmoid_activation,
        'hard_tanh': hard_tanh_activation,
        'softmax': softmax_activation,
        'log_softmax': log_softmax_activation,
    }
    
    activation_lower = activation.lower()
    if activation_lower not in activation_map:
        raise ValueError(f"Unknown activation: {activation}")
    
    return activation_map[activation_lower]


# ==================== CONVENIENT ALIASES ====================

# Aliases without _activation suffix for convenience
sigmoid = sigmoid_activation
tanh = tanh_activation
relu = relu_activation
leaky_relu = leaky_relu_activation
elu = elu_activation
selu = selu_activation
gelu = gelu_activation
swish = swish_activation
mish = mish_activation
softplus = softplus_activation
softsign = softsign_activation
hard_sigmoid = hard_sigmoid_activation
hard_tanh = hard_tanh_activation
softmax = softmax_activation
log_softmax = log_softmax_activation
