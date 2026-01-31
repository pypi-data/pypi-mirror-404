"""
Positional Encoding and Advanced Attention Mechanisms Module

This module provides comprehensive implementations of positional encoding techniques
and advanced attention mechanisms used in modern transformer architectures.

Features:
- Sinusoidal Positional Encoding (original Transformer)
- Learned Positional Embeddings
- Relative Positional Encoding
- Rotary Position Embedding (RoPE)
- ALiBi (Attention with Linear Biases)
- Multi-Head Attention
- Scaled Dot-Product Attention
- Cross Attention
- Self Attention
- Causal (Masked) Attention

Author: Ali Mehdi
License: MIT
"""

import numpy as np
from typing import Optional, Tuple, Union


# ============================================================================
# POSITIONAL ENCODING IMPLEMENTATIONS
# ============================================================================

class SinusoidalPositionalEncoding:
    """
    Sinusoidal Positional Encoding from "Attention Is All You Need"
    
    Uses sine and cosine functions of different frequencies to encode positions.
    
    PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    
    Args:
        d_model: Dimension of the model (embedding size)
        max_len: Maximum sequence length
        dropout: Dropout rate (default: 0.1)
    """
    
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        self.d_model = d_model
        self.max_len = max_len
        self.dropout = dropout
        
        # Precompute positional encodings
        self.pe = self._create_positional_encoding()
    
    def _create_positional_encoding(self) -> np.ndarray:
        """Create the positional encoding matrix"""
        pe = np.zeros((self.max_len, self.d_model))
        position = np.arange(0, self.max_len).reshape(-1, 1)
        
        # Create division term for different frequencies
        div_term = np.exp(np.arange(0, self.d_model, 2) * 
                         -(np.log(10000.0) / self.d_model))
        
        # Apply sine to even indices
        pe[:, 0::2] = np.sin(position * div_term)
        
        # Apply cosine to odd indices
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Add positional encoding to input embeddings
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
        
        Returns:
            Tensor with positional encoding added
        """
        seq_len = x.shape[1]
        
        # Add positional encoding
        x = x + self.pe[:seq_len, :]
        
        # Apply dropout
        if self.dropout > 0:
            mask = np.random.binomial(1, 1 - self.dropout, x.shape)
            x = x * mask / (1 - self.dropout)
        
        return x
    
    def get_encoding(self, positions: np.ndarray) -> np.ndarray:
        """
        Get positional encoding for specific positions
        
        Args:
            positions: Array of position indices
        
        Returns:
            Positional encodings for the given positions
        """
        return self.pe[positions]


class LearnedPositionalEmbedding:
    """
    Learned Positional Embeddings
    
    Instead of fixed sinusoidal patterns, this learns optimal position
    representations during training.
    
    Args:
        max_len: Maximum sequence length
        d_model: Dimension of the model
    """
    
    def __init__(self, max_len: int, d_model: int):
        self.max_len = max_len
        self.d_model = d_model
        
        # Initialize learnable embeddings
        self.embeddings = np.random.randn(max_len, d_model) * 0.02
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Add learned positional embeddings to input
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
        
        Returns:
            Tensor with positional embeddings added
        """
        seq_len = x.shape[1]
        return x + self.embeddings[:seq_len, :]
    
    def update_embeddings(self, gradients: np.ndarray, learning_rate: float = 0.001):
        """Update embeddings using gradients"""
        self.embeddings -= learning_rate * gradients


class RelativePositionalEncoding:
    """
    Relative Positional Encoding (used in T5, Transformer-XL)
    
    Instead of absolute positions, encodes relative distances between tokens.
    This allows better generalization to longer sequences.
    
    Args:
        d_model: Dimension of the model
        max_relative_position: Maximum relative position to consider
    """
    
    def __init__(self, d_model: int, max_relative_position: int = 128):
        self.d_model = d_model
        self.max_relative_position = max_relative_position
        
        # Create relative position embeddings
        vocab_size = 2 * max_relative_position + 1
        self.embeddings = np.random.randn(vocab_size, d_model) * 0.02
    
    def _relative_position_bucket(self, relative_position: np.ndarray) -> np.ndarray:
        """
        Convert relative positions to bucket indices
        
        Buckets are distributed logarithmically for larger distances
        """
        # Clip to max relative position
        relative_position = np.clip(
            relative_position,
            -self.max_relative_position,
            self.max_relative_position
        )
        
        # Shift to make all values positive
        return relative_position + self.max_relative_position
    
    def forward(self, seq_len: int) -> np.ndarray:
        """
        Generate relative positional encodings for a sequence
        
        Args:
            seq_len: Length of the sequence
        
        Returns:
            Relative position encodings of shape (seq_len, seq_len, d_model)
        """
        # Create relative position matrix
        positions = np.arange(seq_len)
        relative_positions = positions[:, None] - positions[None, :]
        
        # Convert to buckets
        buckets = self._relative_position_bucket(relative_positions)
        
        # Get embeddings
        return self.embeddings[buckets]


class RotaryPositionalEmbedding:
    """
    Rotary Position Embedding (RoPE) - used in LLaMA, GPT-NeoX
    
    Applies rotation matrices to encode positions, allowing the model
    to naturally capture relative positions through dot products.
    
    Args:
        d_model: Dimension of the model (must be even)
        max_len: Maximum sequence length
        base: Base for the frequency calculation (default: 10000)
    """
    
    def __init__(self, d_model: int, max_len: int = 2048, base: float = 10000.0):
        assert d_model % 2 == 0, "d_model must be even for RoPE"
        
        self.d_model = d_model
        self.max_len = max_len
        self.base = base
        
        # Precompute rotation matrices
        self.cos_cached, self.sin_cached = self._create_rotation_matrices()
    
    def _create_rotation_matrices(self) -> Tuple[np.ndarray, np.ndarray]:
        """Create cosine and sine matrices for rotation"""
        # Calculate inverse frequencies
        inv_freq = 1.0 / (self.base ** (np.arange(0, self.d_model, 2) / self.d_model))
        
        # Create position indices
        positions = np.arange(self.max_len)
        
        # Calculate angles
        angles = np.outer(positions, inv_freq)
        
        # Create cos and sin matrices
        cos = np.cos(angles)
        sin = np.sin(angles)
        
        return cos, sin
    
    def rotate_half(self, x: np.ndarray) -> np.ndarray:
        """Rotate half the hidden dims of the input"""
        x1 = x[..., :x.shape[-1] // 2]
        x2 = x[..., x.shape[-1] // 2:]
        return np.concatenate([-x2, x1], axis=-1)
    
    def forward(self, x: np.ndarray, positions: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply rotary positional embedding
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            positions: Optional position indices
        
        Returns:
            Tensor with RoPE applied
        """
        seq_len = x.shape[1]
        
        if positions is None:
            positions = np.arange(seq_len)
        
        # Get cos and sin for these positions
        cos = self.cos_cached[positions]
        sin = self.sin_cached[positions]
        
        # Expand dimensions for broadcasting
        cos = np.repeat(cos, 2, axis=-1)
        sin = np.repeat(sin, 2, axis=-1)
        
        # Apply rotation
        return x * cos + self.rotate_half(x) * sin


class ALiBiPositionalBias:
    """
    Attention with Linear Biases (ALiBi)
    
    Instead of adding positional information to embeddings, ALiBi adds
    a bias to attention scores based on distance between tokens.
    
    Args:
        num_heads: Number of attention heads
        max_len: Maximum sequence length
    """
    
    def __init__(self, num_heads: int, max_len: int = 2048):
        self.num_heads = num_heads
        self.max_len = max_len
        
        # Create slopes for each head
        self.slopes = self._get_slopes()
        
        # Precompute bias matrix
        self.bias = self._create_bias_matrix()
    
    def _get_slopes(self) -> np.ndarray:
        """
        Calculate slopes for each attention head
        
        Slopes are geometric sequence: 2^(-8/n), 2^(-16/n), ...
        """
        def get_slopes_power_of_2(n):
            start = 2 ** (-2 ** -(np.log2(n) - 3))
            ratio = start
            return start * ratio ** np.arange(n)
        
        # Handle non-power-of-2 number of heads
        if np.log2(self.num_heads).is_integer():
            return get_slopes_power_of_2(self.num_heads)
        else:
            closest_power_of_2 = 2 ** np.floor(np.log2(self.num_heads))
            slopes = get_slopes_power_of_2(int(closest_power_of_2))
            extra_slopes = get_slopes_power_of_2(int(2 * closest_power_of_2))
            extra_slopes = extra_slopes[::2][:self.num_heads - int(closest_power_of_2)]
            return np.concatenate([slopes, extra_slopes])
    
    def _create_bias_matrix(self) -> np.ndarray:
        """Create the bias matrix for all positions"""
        # Create distance matrix
        positions = np.arange(self.max_len)
        distances = positions[:, None] - positions[None, :]
        
        # Apply slopes to distances
        bias = distances[None, :, :] * self.slopes[:, None, None]
        
        return bias
    
    def forward(self, attention_scores: np.ndarray, seq_len: int) -> np.ndarray:
        """
        Add ALiBi bias to attention scores
        
        Args:
            attention_scores: Attention scores of shape (batch, heads, seq_len, seq_len)
            seq_len: Current sequence length
        
        Returns:
            Attention scores with ALiBi bias added
        """
        return attention_scores + self.bias[:, :seq_len, :seq_len]


# ============================================================================
# ATTENTION MECHANISMS
# ============================================================================

def scaled_dot_product_attention(
    query: np.ndarray,
    key: np.ndarray,
    value: np.ndarray,
    mask: Optional[np.ndarray] = None,
    dropout: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scaled Dot-Product Attention
    
    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V
    
    Args:
        query: Query tensor of shape (..., seq_len_q, d_k)
        key: Key tensor of shape (..., seq_len_k, d_k)
        value: Value tensor of shape (..., seq_len_v, d_v)
        mask: Optional mask tensor
        dropout: Dropout rate
    
    Returns:
        Tuple of (attention_output, attention_weights)
    """
    d_k = query.shape[-1]
    
    # Calculate attention scores
    scores = np.matmul(query, key.transpose(0, 1, 3, 2)) / np.sqrt(d_k)
    
    # Apply mask if provided
    if mask is not None:
        scores = np.where(mask == 0, -1e9, scores)
    
    # Apply softmax
    attention_weights = softmax(scores, axis=-1)
    
    # Apply dropout
    if dropout > 0:
        mask = np.random.binomial(1, 1 - dropout, attention_weights.shape)
        attention_weights = attention_weights * mask / (1 - dropout)
    
    # Apply attention to values
    output = np.matmul(attention_weights, value)
    
    return output, attention_weights


class MultiHeadAttention:
    """
    Multi-Head Attention mechanism
    
    Allows the model to jointly attend to information from different
    representation subspaces at different positions.
    
    Args:
        d_model: Dimension of the model
        num_heads: Number of attention heads
        dropout: Dropout rate
    """
    
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.dropout = dropout
        
        # Initialize weight matrices
        self.W_q = np.random.randn(d_model, d_model) * 0.02
        self.W_k = np.random.randn(d_model, d_model) * 0.02
        self.W_v = np.random.randn(d_model, d_model) * 0.02
        self.W_o = np.random.randn(d_model, d_model) * 0.02
    
    def split_heads(self, x: np.ndarray) -> np.ndarray:
        """Split the last dimension into (num_heads, d_k)"""
        batch_size, seq_len, d_model = x.shape
        x = x.reshape(batch_size, seq_len, self.num_heads, self.d_k)
        return x.transpose(0, 2, 1, 3)  # (batch, heads, seq_len, d_k)
    
    def combine_heads(self, x: np.ndarray) -> np.ndarray:
        """Combine heads back to original shape"""
        batch_size, num_heads, seq_len, d_k = x.shape
        x = x.transpose(0, 2, 1, 3)  # (batch, seq_len, heads, d_k)
        return x.reshape(batch_size, seq_len, self.d_model)
    
    def forward(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass of multi-head attention
        
        Args:
            query: Query tensor
            key: Key tensor
            value: Value tensor
            mask: Optional attention mask
        
        Returns:
            Tuple of (output, attention_weights)
        """
        batch_size = query.shape[0]
        
        # Linear projections
        Q = np.matmul(query, self.W_q)
        K = np.matmul(key, self.W_k)
        V = np.matmul(value, self.W_v)
        
        # Split into multiple heads
        Q = self.split_heads(Q)
        K = self.split_heads(K)
        V = self.split_heads(V)
        
        # Apply scaled dot-product attention
        attention_output, attention_weights = scaled_dot_product_attention(
            Q, K, V, mask, self.dropout
        )
        
        # Combine heads
        attention_output = self.combine_heads(attention_output)
        
        # Final linear projection
        output = np.matmul(attention_output, self.W_o)
        
        return output, attention_weights


class CausalAttention(MultiHeadAttention):
    """
    Causal (Masked) Self-Attention
    
    Prevents positions from attending to subsequent positions.
    Used in autoregressive models like GPT.
    """
    
    def create_causal_mask(self, seq_len: int) -> np.ndarray:
        """Create causal mask to prevent attending to future positions"""
        mask = np.tril(np.ones((seq_len, seq_len)))
        return mask
    
    def forward(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Forward pass with causal masking"""
        seq_len = query.shape[1]
        causal_mask = self.create_causal_mask(seq_len)
        
        if mask is not None:
            mask = mask * causal_mask
        else:
            mask = causal_mask
        
        return super().forward(query, key, value, mask)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable softmax"""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def create_padding_mask(seq: np.ndarray, pad_token: int = 0) -> np.ndarray:
    """
    Create padding mask for sequences
    
    Args:
        seq: Sequence tensor
        pad_token: Token ID used for padding
    
    Returns:
        Mask tensor (1 for real tokens, 0 for padding)
    """
    return (seq != pad_token).astype(np.float32)


def create_look_ahead_mask(size: int) -> np.ndarray:
    """
    Create look-ahead mask for decoder self-attention
    
    Args:
        size: Sequence length
    
    Returns:
        Lower triangular mask
    """
    return np.tril(np.ones((size, size)))


# ============================================================================
# ALIASES FOR CONVENIENCE
# ============================================================================

# Positional Encoding aliases
sinusoidal_pe = SinusoidalPositionalEncoding
learned_pe = LearnedPositionalEmbedding
relative_pe = RelativePositionalEncoding
rope = RotaryPositionalEmbedding
alibi = ALiBiPositionalBias

# Attention aliases
mha = MultiHeadAttention
causal_attn = CausalAttention
sdpa = scaled_dot_product_attention


__all__ = [
    # Positional Encoding Classes
    'SinusoidalPositionalEncoding',
    'LearnedPositionalEmbedding',
    'RelativePositionalEncoding',
    'RotaryPositionalEmbedding',
    'ALiBiPositionalBias',
    # Attention Classes
    'MultiHeadAttention',
    'CausalAttention',
    # Attention Functions
    'scaled_dot_product_attention',
    # Utility Functions
    'softmax',
    'create_padding_mask',
    'create_look_ahead_mask',
    # Aliases
    'sinusoidal_pe',
    'learned_pe',
    'relative_pe',
    'rope',
    'alibi',
    'mha',
    'causal_attn',
    'sdpa',
]
