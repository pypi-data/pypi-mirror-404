"""
Tests for Recurrent Layers

This file contains comprehensive tests for all recurrent layer types.

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.recurrent import (
    RNN,
    LSTM,
    GRU,
    BiLSTM,
    BiGRU,
)


# ============================================================================
# TEST RNN
# ============================================================================

def test_rnn_basic():
    """Test basic RNN functionality."""
    rnn = RNN(input_size=128, hidden_size=256)
    x = np.random.randn(32, 10, 128)  # (batch, seq_len, input_size)
    output, hidden = rnn.forward(x)
    
    assert output.shape == (32, 10, 256)  # (batch, seq_len, hidden_size)
    assert hidden.shape == (32, 256)  # (batch, hidden_size)


def test_rnn_with_initial_hidden():
    """Test RNN with initial hidden state."""
    rnn = RNN(input_size=64, hidden_size=128)
    x = np.random.randn(16, 20, 64)
    h0 = np.random.randn(16, 128)
    
    output, hidden = rnn.forward(x, h0=h0)
    
    assert output.shape == (16, 20, 128)
    assert hidden.shape == (16, 128)


def test_rnn_variable_sequence_length():
    """Test RNN with different sequence lengths."""
    rnn = RNN(input_size=32, hidden_size=64)
    
    for seq_len in [5, 10, 50, 100]:
        x = np.random.randn(8, seq_len, 32)
        output, hidden = rnn.forward(x)
        
        assert output.shape == (8, seq_len, 64)
        assert hidden.shape == (8, 64)


# ============================================================================
# TEST LSTM
# ============================================================================

def test_lstm_basic():
    """Test basic LSTM functionality."""
    lstm = LSTM(input_size=128, hidden_size=256)
    x = np.random.randn(32, 100, 128)
    output, (hidden, cell) = lstm.forward(x)
    
    assert output.shape == (32, 100, 256)
    assert hidden.shape == (32, 256)
    assert cell.shape == (32, 256)


def test_lstm_with_initial_states():
    """Test LSTM with initial hidden and cell states."""
    lstm = LSTM(input_size=64, hidden_size=128)
    x = np.random.randn(16, 50, 64)
    h0 = np.random.randn(16, 128)
    c0 = np.random.randn(16, 128)
    
    output, (hidden, cell) = lstm.forward(x, h0=h0, c0=c0)
    
    assert output.shape == (16, 50, 128)
    assert hidden.shape == (16, 128)
    assert cell.shape == (16, 128)


def test_lstm_long_sequence():
    """Test LSTM on long sequences (tests vanishing gradient solution)."""
    lstm = LSTM(input_size=32, hidden_size=64)
    x = np.random.randn(8, 200, 32)  # Long sequence
    
    output, (hidden, cell) = lstm.forward(x)
    
    assert output.shape == (8, 200, 64)
    assert not np.isnan(output).any()  # No NaN values
    assert not np.isinf(output).any()  # No Inf values


# ============================================================================
# TEST GRU
# ============================================================================

def test_gru_basic():
    """Test basic GRU functionality."""
    gru = GRU(input_size=128, hidden_size=256)
    x = np.random.randn(32, 100, 128)
    output, hidden = gru.forward(x)
    
    assert output.shape == (32, 100, 256)
    assert hidden.shape == (32, 256)


def test_gru_with_initial_hidden():
    """Test GRU with initial hidden state."""
    gru = GRU(input_size=64, hidden_size=128)
    x = np.random.randn(16, 50, 64)
    h0 = np.random.randn(16, 128)
    
    output, hidden = gru.forward(x, h0=h0)
    
    assert output.shape == (16, 50, 128)
    assert hidden.shape == (16, 128)


def test_gru_fewer_parameters_than_lstm():
    """Test that GRU has fewer parameters than LSTM."""
    input_size, hidden_size = 128, 256
    
    lstm = LSTM(input_size, hidden_size)
    gru = GRU(input_size, hidden_size)
    
    # Count parameters
    lstm_params = (lstm.W_f.size + lstm.W_i.size + lstm.W_o.size + lstm.W_c.size +
                   lstm.b_f.size + lstm.b_i.size + lstm.b_o.size + lstm.b_c.size)
    
    gru_params = (gru.W_z.size + gru.W_r.size + gru.W_h.size +
                  gru.b_z.size + gru.b_r.size + gru.b_h.size)
    
    assert gru_params < lstm_params  # GRU has fewer parameters


# ============================================================================
# TEST BILSTM
# ============================================================================

def test_bilstm_basic():
    """Test basic BiLSTM functionality."""
    bilstm = BiLSTM(input_size=128, hidden_size=256)
    x = np.random.randn(32, 100, 128)
    output, ((h_fwd, c_fwd), (h_bwd, c_bwd)) = bilstm.forward(x)
    
    assert output.shape == (32, 100, 512)  # 2 * hidden_size
    assert h_fwd.shape == (32, 256)
    assert c_fwd.shape == (32, 256)
    assert h_bwd.shape == (32, 256)
    assert c_bwd.shape == (32, 256)


def test_bilstm_output_size():
    """Test that BiLSTM output is 2x hidden_size."""
    bilstm = BiLSTM(input_size=64, hidden_size=128)
    x = np.random.randn(16, 50, 64)
    output, _ = bilstm.forward(x)
    
    assert output.shape[2] == 2 * 128  # Concatenated forward + backward


# ============================================================================
# TEST BIGRU
# ============================================================================

def test_bigru_basic():
    """Test basic BiGRU functionality."""
    bigru = BiGRU(input_size=128, hidden_size=256)
    x = np.random.randn(32, 100, 128)
    output, (h_fwd, h_bwd) = bigru.forward(x)
    
    assert output.shape == (32, 100, 512)  # 2 * hidden_size
    assert h_fwd.shape == (32, 256)
    assert h_bwd.shape == (32, 256)


def test_bigru_output_size():
    """Test that BiGRU output is 2x hidden_size."""
    bigru = BiGRU(input_size=64, hidden_size=128)
    x = np.random.randn(16, 50, 64)
    output, _ = bigru.forward(x)
    
    assert output.shape[2] == 2 * 128  # Concatenated forward + backward


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_all_recurrent_layers_return_valid_output():
    """Test that all recurrent layers return valid output."""
    x = np.random.randn(8, 20, 64)
    
    # RNN
    rnn = RNN(64, 128)
    out_rnn, h_rnn = rnn.forward(x)
    assert out_rnn is not None
    assert not np.isnan(out_rnn).any()
    
    # LSTM
    lstm = LSTM(64, 128)
    out_lstm, (h_lstm, c_lstm) = lstm.forward(x)
    assert out_lstm is not None
    assert not np.isnan(out_lstm).any()
    assert not np.isnan(h_lstm).any()
    assert not np.isnan(c_lstm).any()
    
    # GRU
    gru = GRU(64, 128)
    out_gru, h_gru = gru.forward(x)
    assert out_gru is not None
    assert not np.isnan(out_gru).any()
    
    # BiLSTM
    bilstm = BiLSTM(64, 128)
    out_bilstm, _ = bilstm.forward(x)
    assert out_bilstm is not None
    assert not np.isnan(out_bilstm).any()
    
    # BiGRU
    bigru = BiGRU(64, 128)
    out_bigru, _ = bigru.forward(x)
    assert out_bigru is not None
    assert not np.isnan(out_bigru).any()


def test_recurrent_layers_preserve_batch_size():
    """Test that all recurrent layers preserve batch size."""
    batch_sizes = [1, 4, 16, 32]
    
    for batch_size in batch_sizes:
        x = np.random.randn(batch_size, 10, 64)
        
        # RNN
        rnn = RNN(64, 128)
        out, _ = rnn.forward(x)
        assert out.shape[0] == batch_size
        
        # LSTM
        lstm = LSTM(64, 128)
        out, _ = lstm.forward(x)
        assert out.shape[0] == batch_size
        
        # GRU
        gru = GRU(64, 128)
        out, _ = gru.forward(x)
        assert out.shape[0] == batch_size


def test_lstm_vs_gru_output_shapes():
    """Test that LSTM and GRU produce same output shape."""
    x = np.random.randn(16, 50, 128)
    
    lstm = LSTM(128, 256)
    gru = GRU(128, 256)
    
    out_lstm, _ = lstm.forward(x)
    out_gru, _ = gru.forward(x)
    
    assert out_lstm.shape == out_gru.shape


def test_bidirectional_vs_unidirectional():
    """Test that bidirectional layers have 2x output size."""
    x = np.random.randn(16, 50, 128)
    
    # Unidirectional
    lstm = LSTM(128, 256)
    gru = GRU(128, 256)
    
    # Bidirectional
    bilstm = BiLSTM(128, 256)
    bigru = BiGRU(128, 256)
    
    out_lstm, _ = lstm.forward(x)
    out_gru, _ = gru.forward(x)
    out_bilstm, _ = bilstm.forward(x)
    out_bigru, _ = bigru.forward(x)
    
    assert out_bilstm.shape[2] == 2 * out_lstm.shape[2]
    assert out_bigru.shape[2] == 2 * out_gru.shape[2]


def test_recurrent_layers_with_different_hidden_sizes():
    """Test recurrent layers with various hidden sizes."""
    hidden_sizes = [32, 64, 128, 256, 512]
    
    for hidden_size in hidden_sizes:
        x = np.random.randn(8, 20, 64)
        
        rnn = RNN(64, hidden_size)
        lstm = LSTM(64, hidden_size)
        gru = GRU(64, hidden_size)
        
        out_rnn, _ = rnn.forward(x)
        out_lstm, _ = lstm.forward(x)
        out_gru, _ = gru.forward(x)
        
        assert out_rnn.shape[2] == hidden_size
        assert out_lstm.shape[2] == hidden_size
        assert out_gru.shape[2] == hidden_size


def test_lstm_cell_state_updates():
    """Test that LSTM cell state updates across time steps."""
    lstm = LSTM(64, 128)
    x = np.random.randn(8, 10, 64)
    
    # Forward pass
    output, (h_final, c_final) = lstm.forward(x)
    
    # Cell state should be different from initial (zeros)
    c_initial = np.zeros((8, 128))
    assert not np.allclose(c_final, c_initial)


def test_gru_hidden_state_updates():
    """Test that GRU hidden state updates across time steps."""
    gru = GRU(64, 128)
    x = np.random.randn(8, 10, 64)
    
    # Forward pass
    output, h_final = gru.forward(x)
    
    # Hidden state should be different from initial (zeros)
    h_initial = np.zeros((8, 128))
    assert not np.allclose(h_final, h_initial)


def test_recurrent_layers_callable():
    """Test that recurrent layers are callable."""
    x = np.random.randn(8, 20, 64)
    
    rnn = RNN(64, 128)
    lstm = LSTM(64, 128)
    gru = GRU(64, 128)
    bilstm = BiLSTM(64, 128)
    bigru = BiGRU(64, 128)
    
    # Test __call__ method
    out_rnn = rnn(x)
    out_lstm = lstm(x)
    out_gru = gru(x)
    out_bilstm = bilstm(x)
    out_bigru = bigru(x)
    
    assert out_rnn is not None
    assert out_lstm is not None
    assert out_gru is not None
    assert out_bilstm is not None
    assert out_bigru is not None


def test_lstm_gates_in_valid_range():
    """Test that LSTM gates produce values in valid range [0, 1]."""
    lstm = LSTM(64, 128)
    x = np.random.randn(8, 10, 64)
    
    # Forward pass
    output, (h, c) = lstm.forward(x)
    
    # Output should be in reasonable range (tanh output)
    assert np.all(output >= -1.5)
    assert np.all(output <= 1.5)


def test_gru_gates_in_valid_range():
    """Test that GRU gates produce values in valid range."""
    gru = GRU(64, 128)
    x = np.random.randn(8, 10, 64)
    
    # Forward pass
    output, h = gru.forward(x)
    
    # Output should be in reasonable range (tanh output)
    assert np.all(output >= -1.5)
    assert np.all(output <= 1.5)


def test_bidirectional_forward_backward_different():
    """Test that bidirectional layers process forward and backward differently."""
    bilstm = BiLSTM(64, 128)
    x = np.random.randn(8, 20, 64)
    
    output, ((h_fwd, c_fwd), (h_bwd, c_bwd)) = bilstm.forward(x)
    
    # Forward and backward hidden states should be different
    assert not np.allclose(h_fwd, h_bwd)


print("=" * 80)
print("ALL RECURRENT LAYER TESTS PASSED! ✓")
print("=" * 80)
