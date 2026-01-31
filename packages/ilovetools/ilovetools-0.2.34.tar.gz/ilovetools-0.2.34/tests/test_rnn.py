"""
Tests for RNN operations module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.rnn import (
    # Basic RNN
    rnn_cell_forward,
    rnn_forward,
    # LSTM
    lstm_cell_forward,
    lstm_forward,
    # GRU
    gru_cell_forward,
    gru_forward,
    # Bidirectional
    bidirectional_rnn_forward,
    # Utilities
    sigmoid,
    initialize_rnn_weights,
    clip_gradients,
    # Aliases
    vanilla_rnn,
    lstm,
    gru,
    bidirectional_rnn,
)


def test_rnn_cell_forward():
    """Test basic RNN cell forward pass"""
    print("Testing rnn_cell_forward...")
    
    batch_size = 32
    input_size = 128
    hidden_size = 256
    
    x_t = np.random.randn(batch_size, input_size)
    h_prev = np.random.randn(batch_size, hidden_size)
    W_xh = np.random.randn(input_size, hidden_size) * 0.01
    W_hh = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h = np.zeros(hidden_size)
    
    h_t = rnn_cell_forward(x_t, h_prev, W_xh, W_hh, b_h)
    
    assert h_t.shape == (batch_size, hidden_size), "Output shape incorrect"
    assert np.all(np.abs(h_t) <= 1.0), "tanh output should be in [-1, 1]"
    
    print("✓ rnn_cell_forward passed")


def test_rnn_forward():
    """Test basic RNN forward pass"""
    print("Testing rnn_forward...")
    
    batch_size = 32
    seq_len = 10
    input_size = 128
    hidden_size = 256
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0 = np.zeros((batch_size, hidden_size))
    W_xh = np.random.randn(input_size, hidden_size) * 0.01
    W_hh = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h = np.zeros(hidden_size)
    
    outputs, hidden_states = rnn_forward(x, h_0, W_xh, W_hh, b_h)
    
    assert outputs.shape == (batch_size, seq_len, hidden_size), "Outputs shape incorrect"
    assert hidden_states.shape == (batch_size, seq_len, hidden_size), "Hidden states shape incorrect"
    
    print("✓ rnn_forward passed")


def test_lstm_cell_forward():
    """Test LSTM cell forward pass"""
    print("Testing lstm_cell_forward...")
    
    batch_size = 32
    input_size = 128
    hidden_size = 256
    
    x_t = np.random.randn(batch_size, input_size)
    h_prev = np.random.randn(batch_size, hidden_size)
    c_prev = np.random.randn(batch_size, hidden_size)
    
    # Initialize weights
    concat_size = hidden_size + input_size
    W_f = np.random.randn(concat_size, hidden_size) * 0.01
    W_i = np.random.randn(concat_size, hidden_size) * 0.01
    W_c = np.random.randn(concat_size, hidden_size) * 0.01
    W_o = np.random.randn(concat_size, hidden_size) * 0.01
    b_f = np.zeros(hidden_size)
    b_i = np.zeros(hidden_size)
    b_c = np.zeros(hidden_size)
    b_o = np.zeros(hidden_size)
    
    h_t, c_t = lstm_cell_forward(x_t, h_prev, c_prev, W_f, W_i, W_c, W_o, b_f, b_i, b_c, b_o)
    
    assert h_t.shape == (batch_size, hidden_size), "Hidden state shape incorrect"
    assert c_t.shape == (batch_size, hidden_size), "Cell state shape incorrect"
    
    print("✓ lstm_cell_forward passed")


def test_lstm_forward():
    """Test LSTM forward pass"""
    print("Testing lstm_forward...")
    
    batch_size = 32
    seq_len = 10
    input_size = 128
    hidden_size = 256
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0 = np.zeros((batch_size, hidden_size))
    c_0 = np.zeros((batch_size, hidden_size))
    
    # Initialize weights
    concat_size = hidden_size + input_size
    W_f = np.random.randn(concat_size, hidden_size) * 0.01
    W_i = np.random.randn(concat_size, hidden_size) * 0.01
    W_c = np.random.randn(concat_size, hidden_size) * 0.01
    W_o = np.random.randn(concat_size, hidden_size) * 0.01
    b_f = np.zeros(hidden_size)
    b_i = np.zeros(hidden_size)
    b_c = np.zeros(hidden_size)
    b_o = np.zeros(hidden_size)
    
    outputs, hidden_states, cell_states = lstm_forward(
        x, h_0, c_0, W_f, W_i, W_c, W_o, b_f, b_i, b_c, b_o
    )
    
    assert outputs.shape == (batch_size, seq_len, hidden_size), "Outputs shape incorrect"
    assert hidden_states.shape == (batch_size, seq_len, hidden_size), "Hidden states shape incorrect"
    assert cell_states.shape == (batch_size, seq_len, hidden_size), "Cell states shape incorrect"
    
    print("✓ lstm_forward passed")


def test_gru_cell_forward():
    """Test GRU cell forward pass"""
    print("Testing gru_cell_forward...")
    
    batch_size = 32
    input_size = 128
    hidden_size = 256
    
    x_t = np.random.randn(batch_size, input_size)
    h_prev = np.random.randn(batch_size, hidden_size)
    
    # Initialize weights
    concat_size = hidden_size + input_size
    W_z = np.random.randn(concat_size, hidden_size) * 0.01
    W_r = np.random.randn(concat_size, hidden_size) * 0.01
    W_h = np.random.randn(concat_size, hidden_size) * 0.01
    b_z = np.zeros(hidden_size)
    b_r = np.zeros(hidden_size)
    b_h = np.zeros(hidden_size)
    
    h_t = gru_cell_forward(x_t, h_prev, W_z, W_r, W_h, b_z, b_r, b_h)
    
    assert h_t.shape == (batch_size, hidden_size), "Hidden state shape incorrect"
    
    print("✓ gru_cell_forward passed")


def test_gru_forward():
    """Test GRU forward pass"""
    print("Testing gru_forward...")
    
    batch_size = 32
    seq_len = 10
    input_size = 128
    hidden_size = 256
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0 = np.zeros((batch_size, hidden_size))
    
    # Initialize weights
    concat_size = hidden_size + input_size
    W_z = np.random.randn(concat_size, hidden_size) * 0.01
    W_r = np.random.randn(concat_size, hidden_size) * 0.01
    W_h = np.random.randn(concat_size, hidden_size) * 0.01
    b_z = np.zeros(hidden_size)
    b_r = np.zeros(hidden_size)
    b_h = np.zeros(hidden_size)
    
    outputs, hidden_states = gru_forward(x, h_0, W_z, W_r, W_h, b_z, b_r, b_h)
    
    assert outputs.shape == (batch_size, seq_len, hidden_size), "Outputs shape incorrect"
    assert hidden_states.shape == (batch_size, seq_len, hidden_size), "Hidden states shape incorrect"
    
    print("✓ gru_forward passed")


def test_bidirectional_rnn_forward():
    """Test bidirectional RNN forward pass"""
    print("Testing bidirectional_rnn_forward...")
    
    batch_size = 32
    seq_len = 10
    input_size = 128
    hidden_size = 256
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0_f = np.zeros((batch_size, hidden_size))
    h_0_b = np.zeros((batch_size, hidden_size))
    
    # Initialize weights for forward and backward
    W_xh_f = np.random.randn(input_size, hidden_size) * 0.01
    W_hh_f = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h_f = np.zeros(hidden_size)
    
    W_xh_b = np.random.randn(input_size, hidden_size) * 0.01
    W_hh_b = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h_b = np.zeros(hidden_size)
    
    outputs, forward_states, backward_states = bidirectional_rnn_forward(
        x, h_0_f, h_0_b, W_xh_f, W_hh_f, b_h_f, W_xh_b, W_hh_b, b_h_b
    )
    
    # Output should be concatenation of forward and backward (2 * hidden_size)
    assert outputs.shape == (batch_size, seq_len, 2 * hidden_size), "Outputs shape incorrect"
    assert forward_states.shape == (batch_size, seq_len, hidden_size), "Forward states shape incorrect"
    assert backward_states.shape == (batch_size, seq_len, hidden_size), "Backward states shape incorrect"
    
    print("✓ bidirectional_rnn_forward passed")


def test_sigmoid():
    """Test sigmoid function"""
    print("Testing sigmoid...")
    
    x = np.array([-1000, -1, 0, 1, 1000])
    result = sigmoid(x)
    
    assert np.all(result >= 0) and np.all(result <= 1), "Sigmoid should be in [0, 1]"
    assert np.isclose(result[2], 0.5), "Sigmoid(0) should be 0.5"
    
    print("✓ sigmoid passed")


def test_initialize_rnn_weights():
    """Test RNN weight initialization"""
    print("Testing initialize_rnn_weights...")
    
    input_size = 128
    hidden_size = 256
    
    # Test RNN weights
    weights_rnn = initialize_rnn_weights(input_size, hidden_size, cell_type='rnn')
    assert 'W_xh' in weights_rnn, "RNN weights should have W_xh"
    assert 'W_hh' in weights_rnn, "RNN weights should have W_hh"
    assert 'b_h' in weights_rnn, "RNN weights should have b_h"
    
    # Test LSTM weights
    weights_lstm = initialize_rnn_weights(input_size, hidden_size, cell_type='lstm')
    assert 'W_f' in weights_lstm, "LSTM weights should have W_f"
    assert 'W_i' in weights_lstm, "LSTM weights should have W_i"
    assert 'W_c' in weights_lstm, "LSTM weights should have W_c"
    assert 'W_o' in weights_lstm, "LSTM weights should have W_o"
    
    # Test GRU weights
    weights_gru = initialize_rnn_weights(input_size, hidden_size, cell_type='gru')
    assert 'W_z' in weights_gru, "GRU weights should have W_z"
    assert 'W_r' in weights_gru, "GRU weights should have W_r"
    assert 'W_h' in weights_gru, "GRU weights should have W_h"
    
    print("✓ initialize_rnn_weights passed")


def test_clip_gradients():
    """Test gradient clipping"""
    print("Testing clip_gradients...")
    
    # Create large gradients
    grads = np.random.randn(100, 100) * 10
    
    # Clip to max norm 5.0
    clipped = clip_gradients(grads, max_norm=5.0)
    
    norm = np.linalg.norm(clipped)
    assert norm <= 5.0, "Clipped gradient norm should be <= max_norm"
    
    # Test with small gradients (should not clip)
    small_grads = np.random.randn(10, 10) * 0.1
    clipped_small = clip_gradients(small_grads, max_norm=5.0)
    assert np.allclose(small_grads, clipped_small), "Small gradients should not be clipped"
    
    print("✓ clip_gradients passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    batch_size = 8
    seq_len = 5
    input_size = 64
    hidden_size = 128
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0 = np.zeros((batch_size, hidden_size))
    
    # Test vanilla_rnn alias
    W_xh = np.random.randn(input_size, hidden_size) * 0.01
    W_hh = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h = np.zeros(hidden_size)
    
    out1, h1 = vanilla_rnn(x, h_0, W_xh, W_hh, b_h)
    out2, h2 = rnn_forward(x, h_0, W_xh, W_hh, b_h)
    assert np.allclose(out1, out2), "vanilla_rnn alias should work"
    
    print("✓ aliases passed")


def test_rnn_sequence_processing():
    """Test that RNN processes sequences correctly"""
    print("Testing RNN sequence processing...")
    
    batch_size = 4
    seq_len = 5
    input_size = 32
    hidden_size = 64
    
    x = np.random.randn(batch_size, seq_len, input_size)
    h_0 = np.zeros((batch_size, hidden_size))
    W_xh = np.random.randn(input_size, hidden_size) * 0.01
    W_hh = np.random.randn(hidden_size, hidden_size) * 0.01
    b_h = np.zeros(hidden_size)
    
    outputs, hidden_states = rnn_forward(x, h_0, W_xh, W_hh, b_h)
    
    # Check that each timestep depends on previous
    # (outputs should be different at each timestep)
    assert not np.allclose(outputs[:, 0, :], outputs[:, 1, :]), "Outputs should differ across timesteps"
    
    print("✓ RNN sequence processing passed")


def test_lstm_gates():
    """Test that LSTM gates work correctly"""
    print("Testing LSTM gates...")
    
    batch_size = 4
    input_size = 32
    hidden_size = 64
    
    x_t = np.random.randn(batch_size, input_size)
    h_prev = np.random.randn(batch_size, hidden_size)
    c_prev = np.random.randn(batch_size, hidden_size)
    
    # Initialize weights
    concat_size = hidden_size + input_size
    W_f = np.random.randn(concat_size, hidden_size) * 0.01
    W_i = np.random.randn(concat_size, hidden_size) * 0.01
    W_c = np.random.randn(concat_size, hidden_size) * 0.01
    W_o = np.random.randn(concat_size, hidden_size) * 0.01
    b_f = np.zeros(hidden_size)
    b_i = np.zeros(hidden_size)
    b_c = np.zeros(hidden_size)
    b_o = np.zeros(hidden_size)
    
    h_t, c_t = lstm_cell_forward(x_t, h_prev, c_prev, W_f, W_i, W_c, W_o, b_f, b_i, b_c, b_o)
    
    # Cell state should be updated
    assert not np.allclose(c_t, c_prev), "Cell state should be updated"
    
    # Hidden state should be different from previous
    assert not np.allclose(h_t, h_prev), "Hidden state should be updated"
    
    print("✓ LSTM gates passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RNN OPERATIONS MODULE TESTS")
    print("="*60 + "\n")
    
    # Basic RNN tests
    test_rnn_cell_forward()
    test_rnn_forward()
    test_rnn_sequence_processing()
    
    # LSTM tests
    test_lstm_cell_forward()
    test_lstm_forward()
    test_lstm_gates()
    
    # GRU tests
    test_gru_cell_forward()
    test_gru_forward()
    
    # Bidirectional tests
    test_bidirectional_rnn_forward()
    
    # Utility tests
    test_sigmoid()
    test_initialize_rnn_weights()
    test_clip_gradients()
    
    # Aliases
    test_aliases()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
