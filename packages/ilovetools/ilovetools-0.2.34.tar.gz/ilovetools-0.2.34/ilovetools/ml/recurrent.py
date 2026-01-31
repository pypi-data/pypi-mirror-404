"""
Recurrent Layers Suite

This module implements various recurrent neural network layers for sequence modeling.
Recurrent layers process sequential data by maintaining hidden states across time steps.

Implemented Recurrent Types:
1. RNN - Vanilla Recurrent Neural Network
2. LSTM - Long Short-Term Memory (solves vanishing gradients)
3. GRU - Gated Recurrent Unit (efficient alternative to LSTM)
4. BiLSTM - Bidirectional LSTM (context from both directions)
5. BiGRU - Bidirectional GRU (efficient bidirectional processing)

Key Benefits:
- Sequence modeling (text, audio, time series)
- Long-term dependency learning (LSTM/GRU)
- Solves vanishing gradient problem
- Bidirectional context understanding
- Variable-length sequence support

References:
- RNN: Rumelhart et al., "Learning Internal Representations by Error Propagation" (1986)
- LSTM: Hochreiter & Schmidhuber, "Long Short-Term Memory" (1997)
- GRU: Cho et al., "Learning Phrase Representations using RNN Encoder-Decoder" (2014)
- Bidirectional RNN: Schuster & Paliwal, "Bidirectional Recurrent Neural Networks" (1997)

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
from typing import Tuple, Optional


# ============================================================================
# VANILLA RNN
# ============================================================================

class RNN:
    """
    Vanilla Recurrent Neural Network.
    
    Processes sequences by maintaining a hidden state across time steps.
    Suffers from vanishing gradient problem for long sequences.
    
    Formula:
        h(t) = tanh(W_hh * h(t-1) + W_xh * x(t) + b_h)
        y(t) = W_hy * h(t) + b_y
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state
        bias: Whether to use bias (default: True)
    
    Example:
        >>> rnn = RNN(input_size=128, hidden_size=256)
        >>> x = np.random.randn(32, 10, 128)  # (batch, seq_len, input_size)
        >>> output, hidden = rnn.forward(x)
        >>> print(output.shape)  # (32, 10, 256)
        >>> print(hidden.shape)  # (32, 256)
    
    Use Case:
        Short sequences, simple sequence modeling, baseline
    
    Reference:
        Rumelhart et al., "Learning Internal Representations by Error Propagation" (1986)
    """
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Initialize weights (Xavier initialization)
        self.W_xh = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / (input_size + hidden_size))
        self.W_hh = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / (hidden_size + hidden_size))
        
        if bias:
            self.b_h = np.zeros(hidden_size)
        else:
            self.b_h = None
        
        self.cache = None
    
    def forward(self, x: np.ndarray, h0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
            h0: Initial hidden state (batch, hidden_size). If None, initialized to zeros.
        
        Returns:
            Tuple of (output, hidden_state)
            - output: (batch, seq_len, hidden_size)
            - hidden_state: (batch, hidden_size) - final hidden state
        """
        batch_size, seq_len, input_size = x.shape
        
        if input_size != self.input_size:
            raise ValueError(f"Expected input_size {self.input_size}, got {input_size}")
        
        # Initialize hidden state
        if h0 is None:
            h = np.zeros((batch_size, self.hidden_size))
        else:
            h = h0
        
        # Store outputs for each time step
        outputs = []
        hidden_states = []
        
        # Process sequence
        for t in range(seq_len):
            x_t = x[:, t, :]  # (batch, input_size)
            
            # Compute new hidden state
            h = np.tanh(np.dot(x_t, self.W_xh.T) + np.dot(h, self.W_hh.T))
            
            if self.use_bias:
                h = h + self.b_h
            
            outputs.append(h)
            hidden_states.append(h)
        
        # Stack outputs
        output = np.stack(outputs, axis=1)  # (batch, seq_len, hidden_size)
        
        self.cache = (x, hidden_states)
        return output, h
    
    def __call__(self, x: np.ndarray, h0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        return self.forward(x, h0)


# ============================================================================
# LSTM
# ============================================================================

class LSTM:
    """
    Long Short-Term Memory Network.
    
    Solves vanishing gradient problem using gates and cell state.
    Maintains long-term dependencies effectively.
    
    Gates:
        - Forget gate: f(t) = σ(W_f * [h(t-1), x(t)] + b_f)
        - Input gate: i(t) = σ(W_i * [h(t-1), x(t)] + b_i)
        - Output gate: o(t) = σ(W_o * [h(t-1), x(t)] + b_o)
        - Cell candidate: c̃(t) = tanh(W_c * [h(t-1), x(t)] + b_c)
    
    State Updates:
        - Cell state: c(t) = f(t) ⊙ c(t-1) + i(t) ⊙ c̃(t)
        - Hidden state: h(t) = o(t) ⊙ tanh(c(t))
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state
        bias: Whether to use bias (default: True)
    
    Example:
        >>> lstm = LSTM(input_size=128, hidden_size=256)
        >>> x = np.random.randn(32, 100, 128)  # (batch, seq_len, input_size)
        >>> output, (hidden, cell) = lstm.forward(x)
        >>> print(output.shape)  # (32, 100, 256)
        >>> print(hidden.shape)  # (32, 256)
        >>> print(cell.shape)  # (32, 256)
    
    Use Case:
        Long sequences, NLP, time series, speech recognition
    
    Reference:
        Hochreiter & Schmidhuber, "Long Short-Term Memory" (1997)
    """
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Combined input size (input + hidden)
        combined_size = input_size + hidden_size
        
        # Initialize weights for all gates (Xavier initialization)
        scale = np.sqrt(2.0 / (combined_size + hidden_size))
        
        self.W_f = np.random.randn(hidden_size, combined_size) * scale  # Forget gate
        self.W_i = np.random.randn(hidden_size, combined_size) * scale  # Input gate
        self.W_o = np.random.randn(hidden_size, combined_size) * scale  # Output gate
        self.W_c = np.random.randn(hidden_size, combined_size) * scale  # Cell candidate
        
        if bias:
            self.b_f = np.zeros(hidden_size)
            self.b_i = np.zeros(hidden_size)
            self.b_o = np.zeros(hidden_size)
            self.b_c = np.zeros(hidden_size)
        else:
            self.b_f = self.b_i = self.b_o = self.b_c = None
        
        self.cache = None
    
    def forward(self, x: np.ndarray, 
                h0: Optional[np.ndarray] = None,
                c0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
            h0: Initial hidden state (batch, hidden_size)
            c0: Initial cell state (batch, hidden_size)
        
        Returns:
            Tuple of (output, (hidden_state, cell_state))
            - output: (batch, seq_len, hidden_size)
            - hidden_state: (batch, hidden_size)
            - cell_state: (batch, hidden_size)
        """
        batch_size, seq_len, input_size = x.shape
        
        if input_size != self.input_size:
            raise ValueError(f"Expected input_size {self.input_size}, got {input_size}")
        
        # Initialize hidden and cell states
        if h0 is None:
            h = np.zeros((batch_size, self.hidden_size))
        else:
            h = h0
        
        if c0 is None:
            c = np.zeros((batch_size, self.hidden_size))
        else:
            c = c0
        
        # Store outputs
        outputs = []
        
        # Process sequence
        for t in range(seq_len):
            x_t = x[:, t, :]  # (batch, input_size)
            
            # Concatenate input and hidden state
            combined = np.concatenate([h, x_t], axis=1)  # (batch, hidden_size + input_size)
            
            # Compute gates
            f_t = self._sigmoid(np.dot(combined, self.W_f.T) + (self.b_f if self.use_bias else 0))  # Forget
            i_t = self._sigmoid(np.dot(combined, self.W_i.T) + (self.b_i if self.use_bias else 0))  # Input
            o_t = self._sigmoid(np.dot(combined, self.W_o.T) + (self.b_o if self.use_bias else 0))  # Output
            c_tilde = np.tanh(np.dot(combined, self.W_c.T) + (self.b_c if self.use_bias else 0))  # Cell candidate
            
            # Update cell state
            c = f_t * c + i_t * c_tilde
            
            # Update hidden state
            h = o_t * np.tanh(c)
            
            outputs.append(h)
        
        # Stack outputs
        output = np.stack(outputs, axis=1)  # (batch, seq_len, hidden_size)
        
        return output, (h, c)
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def __call__(self, x: np.ndarray, 
                 h0: Optional[np.ndarray] = None,
                 c0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        return self.forward(x, h0, c0)


# ============================================================================
# GRU
# ============================================================================

class GRU:
    """
    Gated Recurrent Unit.
    
    Simplified alternative to LSTM with fewer parameters.
    Combines forget and input gates into update gate.
    
    Gates:
        - Update gate: z(t) = σ(W_z * [h(t-1), x(t)] + b_z)
        - Reset gate: r(t) = σ(W_r * [h(t-1), x(t)] + b_r)
        - Candidate: h̃(t) = tanh(W_h * [r(t) ⊙ h(t-1), x(t)] + b_h)
    
    State Update:
        h(t) = (1 - z(t)) ⊙ h(t-1) + z(t) ⊙ h̃(t)
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state
        bias: Whether to use bias (default: True)
    
    Example:
        >>> gru = GRU(input_size=128, hidden_size=256)
        >>> x = np.random.randn(32, 100, 128)  # (batch, seq_len, input_size)
        >>> output, hidden = gru.forward(x)
        >>> print(output.shape)  # (32, 100, 256)
        >>> print(hidden.shape)  # (32, 256)
    
    Use Case:
        Efficient sequence modeling, faster training than LSTM
    
    Reference:
        Cho et al., "Learning Phrase Representations using RNN Encoder-Decoder" (2014)
    """
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Combined input size
        combined_size = input_size + hidden_size
        
        # Initialize weights (Xavier initialization)
        scale = np.sqrt(2.0 / (combined_size + hidden_size))
        
        self.W_z = np.random.randn(hidden_size, combined_size) * scale  # Update gate
        self.W_r = np.random.randn(hidden_size, combined_size) * scale  # Reset gate
        self.W_h = np.random.randn(hidden_size, combined_size) * scale  # Candidate
        
        if bias:
            self.b_z = np.zeros(hidden_size)
            self.b_r = np.zeros(hidden_size)
            self.b_h = np.zeros(hidden_size)
        else:
            self.b_z = self.b_r = self.b_h = None
        
        self.cache = None
    
    def forward(self, x: np.ndarray, h0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
            h0: Initial hidden state (batch, hidden_size)
        
        Returns:
            Tuple of (output, hidden_state)
            - output: (batch, seq_len, hidden_size)
            - hidden_state: (batch, hidden_size)
        """
        batch_size, seq_len, input_size = x.shape
        
        if input_size != self.input_size:
            raise ValueError(f"Expected input_size {self.input_size}, got {input_size}")
        
        # Initialize hidden state
        if h0 is None:
            h = np.zeros((batch_size, self.hidden_size))
        else:
            h = h0
        
        # Store outputs
        outputs = []
        
        # Process sequence
        for t in range(seq_len):
            x_t = x[:, t, :]  # (batch, input_size)
            
            # Concatenate input and hidden state
            combined = np.concatenate([h, x_t], axis=1)
            
            # Compute gates
            z_t = self._sigmoid(np.dot(combined, self.W_z.T) + (self.b_z if self.use_bias else 0))  # Update
            r_t = self._sigmoid(np.dot(combined, self.W_r.T) + (self.b_r if self.use_bias else 0))  # Reset
            
            # Compute candidate hidden state
            combined_reset = np.concatenate([r_t * h, x_t], axis=1)
            h_tilde = np.tanh(np.dot(combined_reset, self.W_h.T) + (self.b_h if self.use_bias else 0))
            
            # Update hidden state
            h = (1 - z_t) * h + z_t * h_tilde
            
            outputs.append(h)
        
        # Stack outputs
        output = np.stack(outputs, axis=1)  # (batch, seq_len, hidden_size)
        
        return output, h
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def __call__(self, x: np.ndarray, h0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        return self.forward(x, h0)


# ============================================================================
# BIDIRECTIONAL LSTM
# ============================================================================

class BiLSTM:
    """
    Bidirectional LSTM.
    
    Processes sequence in both forward and backward directions.
    Concatenates outputs from both directions for richer context.
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state (per direction)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> bilstm = BiLSTM(input_size=128, hidden_size=256)
        >>> x = np.random.randn(32, 100, 128)
        >>> output, (hidden_fwd, hidden_bwd) = bilstm.forward(x)
        >>> print(output.shape)  # (32, 100, 512) - 2 * hidden_size
    
    Use Case:
        NLP tasks, named entity recognition, sentiment analysis
    
    Reference:
        Schuster & Paliwal, "Bidirectional Recurrent Neural Networks" (1997)
    """
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Forward and backward LSTMs
        self.lstm_forward = LSTM(input_size, hidden_size, bias)
        self.lstm_backward = LSTM(input_size, hidden_size, bias)
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, Tuple[Tuple, Tuple]]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
        
        Returns:
            Tuple of (output, ((h_fwd, c_fwd), (h_bwd, c_bwd)))
            - output: (batch, seq_len, 2 * hidden_size)
        """
        # Forward direction
        output_fwd, (h_fwd, c_fwd) = self.lstm_forward.forward(x)
        
        # Backward direction (reverse sequence)
        x_reversed = np.flip(x, axis=1)
        output_bwd, (h_bwd, c_bwd) = self.lstm_backward.forward(x_reversed)
        output_bwd = np.flip(output_bwd, axis=1)  # Reverse back
        
        # Concatenate outputs
        output = np.concatenate([output_fwd, output_bwd], axis=2)
        
        return output, ((h_fwd, c_fwd), (h_bwd, c_bwd))
    
    def __call__(self, x: np.ndarray) -> Tuple[np.ndarray, Tuple[Tuple, Tuple]]:
        return self.forward(x)


# ============================================================================
# BIDIRECTIONAL GRU
# ============================================================================

class BiGRU:
    """
    Bidirectional GRU.
    
    Efficient bidirectional processing with GRU cells.
    
    Args:
        input_size: Size of input features
        hidden_size: Size of hidden state (per direction)
        bias: Whether to use bias (default: True)
    
    Example:
        >>> bigru = BiGRU(input_size=128, hidden_size=256)
        >>> x = np.random.randn(32, 100, 128)
        >>> output, (hidden_fwd, hidden_bwd) = bigru.forward(x)
        >>> print(output.shape)  # (32, 100, 512) - 2 * hidden_size
    
    Use Case:
        Efficient bidirectional sequence modeling
    
    Reference:
        Cho et al., "Learning Phrase Representations using RNN Encoder-Decoder" (2014)
    """
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Forward and backward GRUs
        self.gru_forward = GRU(input_size, hidden_size, bias)
        self.gru_backward = GRU(input_size, hidden_size, bias)
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
        
        Returns:
            Tuple of (output, (h_fwd, h_bwd))
            - output: (batch, seq_len, 2 * hidden_size)
        """
        # Forward direction
        output_fwd, h_fwd = self.gru_forward.forward(x)
        
        # Backward direction
        x_reversed = np.flip(x, axis=1)
        output_bwd, h_bwd = self.gru_backward.forward(x_reversed)
        output_bwd = np.flip(output_bwd, axis=1)
        
        # Concatenate outputs
        output = np.concatenate([output_fwd, output_bwd], axis=2)
        
        return output, (h_fwd, h_bwd)
    
    def __call__(self, x: np.ndarray) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        return self.forward(x)


__all__ = [
    'RNN',
    'LSTM',
    'GRU',
    'BiLSTM',
    'BiGRU',
]
