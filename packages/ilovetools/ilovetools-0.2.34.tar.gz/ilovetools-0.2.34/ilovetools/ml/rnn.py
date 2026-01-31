"""
Recurrent Neural Network Operations

This module provides RNN architectures and operations:
- Basic RNN (Vanilla RNN)
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)
- Bidirectional RNNs
- Stacked RNNs
- Sequence-to-Sequence utilities

All operations support batched inputs and are optimized for sequence processing.
"""

import numpy as np
from typing import Tuple, Optional, List


# ============================================================================
# BASIC RNN (VANILLA RNN)
# ============================================================================

def rnn_cell_forward(
    x_t: np.ndarray,
    h_prev: np.ndarray,
    W_xh: np.ndarray,
    W_hh: np.ndarray,
    b_h: np.ndarray
) -> np.ndarray:
    """
    Single timestep of basic RNN cell
    
    Formula: h_t = tanh(W_xh @ x_t + W_hh @ h_prev + b_h)
    
    Args:
        x_t: Input at timestep t, shape (batch, input_size)
        h_prev: Previous hidden state, shape (batch, hidden_size)
        W_xh: Input-to-hidden weights, shape (input_size, hidden_size)
        W_hh: Hidden-to-hidden weights, shape (hidden_size, hidden_size)
        b_h: Hidden bias, shape (hidden_size,)
        
    Returns:
        h_t: New hidden state, shape (batch, hidden_size)
        
    Example:
        >>> x_t = np.random.randn(32, 128)  # (batch, input_size)
        >>> h_prev = np.random.randn(32, 256)  # (batch, hidden_size)
        >>> W_xh = np.random.randn(128, 256)
        >>> W_hh = np.random.randn(256, 256)
        >>> b_h = np.zeros(256)
        >>> h_t = rnn_cell_forward(x_t, h_prev, W_xh, W_hh, b_h)
        >>> print(h_t.shape)  # (32, 256)
    """
    h_t = np.tanh(np.dot(x_t, W_xh) + np.dot(h_prev, W_hh) + b_h)
    return h_t


def rnn_forward(
    x: np.ndarray,
    h_0: np.ndarray,
    W_xh: np.ndarray,
    W_hh: np.ndarray,
    b_h: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forward pass through entire RNN sequence
    
    Args:
        x: Input sequence, shape (batch, seq_len, input_size)
        h_0: Initial hidden state, shape (batch, hidden_size)
        W_xh: Input-to-hidden weights
        W_hh: Hidden-to-hidden weights
        b_h: Hidden bias
        
    Returns:
        Tuple of (outputs, hidden_states)
        - outputs: shape (batch, seq_len, hidden_size)
        - hidden_states: shape (batch, seq_len, hidden_size)
        
    Example:
        >>> x = np.random.randn(32, 10, 128)  # (batch, seq_len, input_size)
        >>> h_0 = np.zeros((32, 256))
        >>> W_xh = np.random.randn(128, 256)
        >>> W_hh = np.random.randn(256, 256)
        >>> b_h = np.zeros(256)
        >>> outputs, hidden_states = rnn_forward(x, h_0, W_xh, W_hh, b_h)
        >>> print(outputs.shape)  # (32, 10, 256)
    """
    batch_size, seq_len, input_size = x.shape
    hidden_size = h_0.shape[1]
    
    # Initialize outputs
    outputs = np.zeros((batch_size, seq_len, hidden_size))
    hidden_states = np.zeros((batch_size, seq_len, hidden_size))
    
    h_t = h_0
    
    # Process sequence
    for t in range(seq_len):
        h_t = rnn_cell_forward(x[:, t, :], h_t, W_xh, W_hh, b_h)
        outputs[:, t, :] = h_t
        hidden_states[:, t, :] = h_t
    
    return outputs, hidden_states


# ============================================================================
# LSTM (LONG SHORT-TERM MEMORY)
# ============================================================================

def lstm_cell_forward(
    x_t: np.ndarray,
    h_prev: np.ndarray,
    c_prev: np.ndarray,
    W_f: np.ndarray,
    W_i: np.ndarray,
    W_c: np.ndarray,
    W_o: np.ndarray,
    b_f: np.ndarray,
    b_i: np.ndarray,
    b_c: np.ndarray,
    b_o: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Single timestep of LSTM cell
    
    LSTM has three gates:
    - Forget gate: decides what to forget from cell state
    - Input gate: decides what new information to store
    - Output gate: decides what to output
    
    Args:
        x_t: Input at timestep t, shape (batch, input_size)
        h_prev: Previous hidden state, shape (batch, hidden_size)
        c_prev: Previous cell state, shape (batch, hidden_size)
        W_f, W_i, W_c, W_o: Weight matrices for gates
        b_f, b_i, b_c, b_o: Bias vectors for gates
        
    Returns:
        Tuple of (h_t, c_t)
        - h_t: New hidden state, shape (batch, hidden_size)
        - c_t: New cell state, shape (batch, hidden_size)
        
    Example:
        >>> x_t = np.random.randn(32, 128)
        >>> h_prev = np.random.randn(32, 256)
        >>> c_prev = np.random.randn(32, 256)
        >>> # Initialize weights...
        >>> h_t, c_t = lstm_cell_forward(x_t, h_prev, c_prev, W_f, W_i, W_c, W_o, b_f, b_i, b_c, b_o)
        >>> print(h_t.shape, c_t.shape)  # (32, 256), (32, 256)
    """
    # Concatenate input and previous hidden state
    concat = np.concatenate([h_prev, x_t], axis=1)
    
    # Forget gate
    f_t = sigmoid(np.dot(concat, W_f) + b_f)
    
    # Input gate
    i_t = sigmoid(np.dot(concat, W_i) + b_i)
    
    # Candidate cell state
    c_tilde = np.tanh(np.dot(concat, W_c) + b_c)
    
    # New cell state
    c_t = f_t * c_prev + i_t * c_tilde
    
    # Output gate
    o_t = sigmoid(np.dot(concat, W_o) + b_o)
    
    # New hidden state
    h_t = o_t * np.tanh(c_t)
    
    return h_t, c_t


def lstm_forward(
    x: np.ndarray,
    h_0: np.ndarray,
    c_0: np.ndarray,
    W_f: np.ndarray,
    W_i: np.ndarray,
    W_c: np.ndarray,
    W_o: np.ndarray,
    b_f: np.ndarray,
    b_i: np.ndarray,
    b_c: np.ndarray,
    b_o: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Forward pass through entire LSTM sequence
    
    Args:
        x: Input sequence, shape (batch, seq_len, input_size)
        h_0: Initial hidden state, shape (batch, hidden_size)
        c_0: Initial cell state, shape (batch, hidden_size)
        W_f, W_i, W_c, W_o: Weight matrices
        b_f, b_i, b_c, b_o: Bias vectors
        
    Returns:
        Tuple of (outputs, hidden_states, cell_states)
        - outputs: shape (batch, seq_len, hidden_size)
        - hidden_states: shape (batch, seq_len, hidden_size)
        - cell_states: shape (batch, seq_len, hidden_size)
        
    Example:
        >>> x = np.random.randn(32, 10, 128)
        >>> h_0 = np.zeros((32, 256))
        >>> c_0 = np.zeros((32, 256))
        >>> # Initialize weights...
        >>> outputs, h_states, c_states = lstm_forward(x, h_0, c_0, W_f, W_i, W_c, W_o, b_f, b_i, b_c, b_o)
        >>> print(outputs.shape)  # (32, 10, 256)
    """
    batch_size, seq_len, input_size = x.shape
    hidden_size = h_0.shape[1]
    
    # Initialize outputs
    outputs = np.zeros((batch_size, seq_len, hidden_size))
    hidden_states = np.zeros((batch_size, seq_len, hidden_size))
    cell_states = np.zeros((batch_size, seq_len, hidden_size))
    
    h_t = h_0
    c_t = c_0
    
    # Process sequence
    for t in range(seq_len):
        h_t, c_t = lstm_cell_forward(
            x[:, t, :], h_t, c_t,
            W_f, W_i, W_c, W_o,
            b_f, b_i, b_c, b_o
        )
        outputs[:, t, :] = h_t
        hidden_states[:, t, :] = h_t
        cell_states[:, t, :] = c_t
    
    return outputs, hidden_states, cell_states


# ============================================================================
# GRU (GATED RECURRENT UNIT)
# ============================================================================

def gru_cell_forward(
    x_t: np.ndarray,
    h_prev: np.ndarray,
    W_z: np.ndarray,
    W_r: np.ndarray,
    W_h: np.ndarray,
    b_z: np.ndarray,
    b_r: np.ndarray,
    b_h: np.ndarray
) -> np.ndarray:
    """
    Single timestep of GRU cell
    
    GRU has two gates:
    - Update gate: decides how much to update
    - Reset gate: decides how much to forget
    
    Args:
        x_t: Input at timestep t, shape (batch, input_size)
        h_prev: Previous hidden state, shape (batch, hidden_size)
        W_z, W_r, W_h: Weight matrices for gates
        b_z, b_r, b_h: Bias vectors for gates
        
    Returns:
        h_t: New hidden state, shape (batch, hidden_size)
        
    Example:
        >>> x_t = np.random.randn(32, 128)
        >>> h_prev = np.random.randn(32, 256)
        >>> # Initialize weights...
        >>> h_t = gru_cell_forward(x_t, h_prev, W_z, W_r, W_h, b_z, b_r, b_h)
        >>> print(h_t.shape)  # (32, 256)
    """
    # Concatenate input and previous hidden state
    concat = np.concatenate([h_prev, x_t], axis=1)
    
    # Update gate
    z_t = sigmoid(np.dot(concat, W_z) + b_z)
    
    # Reset gate
    r_t = sigmoid(np.dot(concat, W_r) + b_r)
    
    # Candidate hidden state
    concat_reset = np.concatenate([r_t * h_prev, x_t], axis=1)
    h_tilde = np.tanh(np.dot(concat_reset, W_h) + b_h)
    
    # New hidden state
    h_t = (1 - z_t) * h_prev + z_t * h_tilde
    
    return h_t


def gru_forward(
    x: np.ndarray,
    h_0: np.ndarray,
    W_z: np.ndarray,
    W_r: np.ndarray,
    W_h: np.ndarray,
    b_z: np.ndarray,
    b_r: np.ndarray,
    b_h: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forward pass through entire GRU sequence
    
    Args:
        x: Input sequence, shape (batch, seq_len, input_size)
        h_0: Initial hidden state, shape (batch, hidden_size)
        W_z, W_r, W_h: Weight matrices
        b_z, b_r, b_h: Bias vectors
        
    Returns:
        Tuple of (outputs, hidden_states)
        - outputs: shape (batch, seq_len, hidden_size)
        - hidden_states: shape (batch, seq_len, hidden_size)
        
    Example:
        >>> x = np.random.randn(32, 10, 128)
        >>> h_0 = np.zeros((32, 256))
        >>> # Initialize weights...
        >>> outputs, hidden_states = gru_forward(x, h_0, W_z, W_r, W_h, b_z, b_r, b_h)
        >>> print(outputs.shape)  # (32, 10, 256)
    """
    batch_size, seq_len, input_size = x.shape
    hidden_size = h_0.shape[1]
    
    # Initialize outputs
    outputs = np.zeros((batch_size, seq_len, hidden_size))
    hidden_states = np.zeros((batch_size, seq_len, hidden_size))
    
    h_t = h_0
    
    # Process sequence
    for t in range(seq_len):
        h_t = gru_cell_forward(
            x[:, t, :], h_t,
            W_z, W_r, W_h,
            b_z, b_r, b_h
        )
        outputs[:, t, :] = h_t
        hidden_states[:, t, :] = h_t
    
    return outputs, hidden_states


# ============================================================================
# BIDIRECTIONAL RNN
# ============================================================================

def bidirectional_rnn_forward(
    x: np.ndarray,
    h_0_forward: np.ndarray,
    h_0_backward: np.ndarray,
    W_xh_f: np.ndarray,
    W_hh_f: np.ndarray,
    b_h_f: np.ndarray,
    W_xh_b: np.ndarray,
    W_hh_b: np.ndarray,
    b_h_b: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bidirectional RNN forward pass
    
    Processes sequence in both forward and backward directions.
    
    Args:
        x: Input sequence, shape (batch, seq_len, input_size)
        h_0_forward: Initial forward hidden state
        h_0_backward: Initial backward hidden state
        W_xh_f, W_hh_f, b_h_f: Forward RNN parameters
        W_xh_b, W_hh_b, b_h_b: Backward RNN parameters
        
    Returns:
        Tuple of (outputs, forward_states, backward_states)
        - outputs: Concatenated forward and backward, shape (batch, seq_len, 2*hidden_size)
        
    Example:
        >>> x = np.random.randn(32, 10, 128)
        >>> h_0_f = np.zeros((32, 256))
        >>> h_0_b = np.zeros((32, 256))
        >>> # Initialize weights...
        >>> outputs, h_f, h_b = bidirectional_rnn_forward(x, h_0_f, h_0_b, W_xh_f, W_hh_f, b_h_f, W_xh_b, W_hh_b, b_h_b)
        >>> print(outputs.shape)  # (32, 10, 512)
    """
    # Forward pass
    forward_outputs, forward_states = rnn_forward(
        x, h_0_forward, W_xh_f, W_hh_f, b_h_f
    )
    
    # Backward pass (reverse sequence)
    x_reversed = np.flip(x, axis=1)
    backward_outputs, backward_states = rnn_forward(
        x_reversed, h_0_backward, W_xh_b, W_hh_b, b_h_b
    )
    backward_outputs = np.flip(backward_outputs, axis=1)
    backward_states = np.flip(backward_states, axis=1)
    
    # Concatenate forward and backward
    outputs = np.concatenate([forward_outputs, backward_outputs], axis=2)
    
    return outputs, forward_states, backward_states


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sigmoid(x: np.ndarray) -> np.ndarray:
    """
    Sigmoid activation function
    
    Args:
        x: Input array
        
    Returns:
        Sigmoid of input
    """
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def initialize_rnn_weights(
    input_size: int,
    hidden_size: int,
    cell_type: str = 'rnn'
) -> dict:
    """
    Initialize RNN weights
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state
        cell_type: Type of RNN cell ('rnn', 'lstm', 'gru')
        
    Returns:
        Dictionary of initialized weights
        
    Example:
        >>> weights = initialize_rnn_weights(128, 256, cell_type='lstm')
        >>> print(weights.keys())
    """
    weights = {}
    
    if cell_type == 'rnn':
        weights['W_xh'] = np.random.randn(input_size, hidden_size) * 0.01
        weights['W_hh'] = np.random.randn(hidden_size, hidden_size) * 0.01
        weights['b_h'] = np.zeros(hidden_size)
        
    elif cell_type == 'lstm':
        concat_size = hidden_size + input_size
        weights['W_f'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['W_i'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['W_c'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['W_o'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['b_f'] = np.zeros(hidden_size)
        weights['b_i'] = np.zeros(hidden_size)
        weights['b_c'] = np.zeros(hidden_size)
        weights['b_o'] = np.zeros(hidden_size)
        
    elif cell_type == 'gru':
        concat_size = hidden_size + input_size
        weights['W_z'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['W_r'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['W_h'] = np.random.randn(concat_size, hidden_size) * 0.01
        weights['b_z'] = np.zeros(hidden_size)
        weights['b_r'] = np.zeros(hidden_size)
        weights['b_h'] = np.zeros(hidden_size)
    
    return weights


def clip_gradients(gradients: np.ndarray, max_norm: float = 5.0) -> np.ndarray:
    """
    Clip gradients to prevent exploding gradients
    
    Args:
        gradients: Gradient array
        max_norm: Maximum gradient norm
        
    Returns:
        Clipped gradients
        
    Example:
        >>> grads = np.random.randn(100, 100) * 10
        >>> clipped = clip_gradients(grads, max_norm=5.0)
        >>> print(np.linalg.norm(clipped))  # <= 5.0
    """
    norm = np.linalg.norm(gradients)
    if norm > max_norm:
        gradients = gradients * (max_norm / norm)
    return gradients


# Aliases for convenience
vanilla_rnn = rnn_forward
lstm = lstm_forward
gru = gru_forward
bidirectional_rnn = bidirectional_rnn_forward
