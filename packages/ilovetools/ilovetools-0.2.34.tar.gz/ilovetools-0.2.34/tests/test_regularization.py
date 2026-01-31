"""
Tests for dropout and regularization techniques module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.regularization import (
    # Dropout
    dropout,
    spatial_dropout,
    variational_dropout,
    dropconnect,
    # L1 Regularization
    l1_regularization,
    l1_gradient,
    l1_penalty,
    # L2 Regularization
    l2_regularization,
    l2_gradient,
    l2_penalty,
    weight_decay,
    # Elastic Net
    elastic_net_regularization,
    elastic_net_gradient,
    elastic_net_penalty,
    # Early Stopping
    EarlyStopping,
    early_stopping_monitor,
    should_stop_early,
    # Utilities
    apply_regularization,
    compute_regularization_gradient,
    get_dropout_rate_schedule,
    # Aliases
    inverted_dropout,
    dropout_mask,
)


def test_dropout_training():
    """Test standard dropout in training mode"""
    print("Testing dropout (training)...")
    
    x = np.random.randn(32, 128)
    output, mask = dropout(x, dropout_rate=0.5, training=True, seed=42)
    
    assert output.shape == x.shape, "Output shape should match input"
    assert mask.shape == x.shape, "Mask shape should match input"
    
    # Check that approximately 50% of neurons are dropped
    dropped_ratio = np.sum(mask == 0) / mask.size
    assert 0.4 < dropped_ratio < 0.6, f"Dropout ratio should be ~0.5, got {dropped_ratio}"
    
    # Check scaling (inverted dropout)
    active_neurons = mask > 0
    if np.any(active_neurons):
        assert np.allclose(output[active_neurons], x[active_neurons] / 0.5), "Inverted dropout scaling incorrect"
    
    print("✓ dropout (training) passed")


def test_dropout_inference():
    """Test standard dropout in inference mode"""
    print("Testing dropout (inference)...")
    
    x = np.random.randn(32, 128)
    output, mask = dropout(x, dropout_rate=0.5, training=False)
    
    assert np.array_equal(output, x), "No dropout should be applied during inference"
    assert np.all(mask == 1), "Mask should be all ones during inference"
    
    print("✓ dropout (inference) passed")


def test_spatial_dropout():
    """Test spatial dropout for CNNs"""
    print("Testing spatial_dropout...")
    
    x = np.random.randn(32, 64, 28, 28)
    output, mask = spatial_dropout(x, dropout_rate=0.2, training=True, seed=42)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check that entire channels are dropped
    for b in range(x.shape[0]):
        for c in range(x.shape[1]):
            channel_mask = mask[b, c]
            # All spatial locations should have same mask value
            assert np.all(channel_mask == channel_mask[0, 0]), "Spatial dropout should drop entire channels"
    
    print("✓ spatial_dropout passed")


def test_variational_dropout():
    """Test variational dropout for RNNs"""
    print("Testing variational_dropout...")
    
    x = np.random.randn(32, 10, 512)
    output, mask = variational_dropout(x, dropout_rate=0.3, training=True, seed=42)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check that same mask is used across time steps
    for b in range(x.shape[0]):
        for f in range(x.shape[2]):
            feature_mask = mask[b, :, f]
            # All time steps should have same mask value
            assert np.all(feature_mask == feature_mask[0]), "Variational dropout should use same mask across time"
    
    print("✓ variational_dropout passed")


def test_dropconnect():
    """Test dropconnect"""
    print("Testing dropconnect...")
    
    x = np.random.randn(32, 128)
    weights = np.random.randn(256, 128)
    
    output, mask = dropconnect(x, weights, dropout_rate=0.5, training=True, seed=42)
    
    assert output.shape == (32, 256), "Output shape incorrect"
    assert mask.shape == weights.shape, "Mask shape should match weights"
    
    # Check that approximately 50% of connections are dropped
    dropped_ratio = np.sum(mask == 0) / mask.size
    assert 0.4 < dropped_ratio < 0.6, f"DropConnect ratio should be ~0.5, got {dropped_ratio}"
    
    print("✓ dropconnect passed")


def test_l1_regularization():
    """Test L1 regularization"""
    print("Testing l1_regularization...")
    
    weights = np.array([[1.0, -2.0], [3.0, -4.0]])
    penalty = l1_regularization(weights, lambda_=0.01)
    
    expected = 0.01 * (1 + 2 + 3 + 4)  # 0.1
    assert np.isclose(penalty, expected), f"L1 penalty incorrect: {penalty} vs {expected}"
    
    print("✓ l1_regularization passed")


def test_l1_gradient():
    """Test L1 gradient"""
    print("Testing l1_gradient...")
    
    weights = np.array([[1.0, -2.0], [0.0, -4.0]])
    grad = l1_gradient(weights, lambda_=0.01)
    
    expected = np.array([[0.01, -0.01], [0.0, -0.01]])
    assert np.allclose(grad, expected), "L1 gradient incorrect"
    
    print("✓ l1_gradient passed")


def test_l2_regularization():
    """Test L2 regularization"""
    print("Testing l2_regularization...")
    
    weights = np.array([[1.0, 2.0], [3.0, 4.0]])
    penalty = l2_regularization(weights, lambda_=0.01)
    
    expected = 0.01 * (1 + 4 + 9 + 16)  # 0.3
    assert np.isclose(penalty, expected), f"L2 penalty incorrect: {penalty} vs {expected}"
    
    print("✓ l2_regularization passed")


def test_l2_gradient():
    """Test L2 gradient"""
    print("Testing l2_gradient...")
    
    weights = np.array([[1.0, 2.0], [3.0, 4.0]])
    grad = l2_gradient(weights, lambda_=0.01)
    
    expected = 2 * 0.01 * weights
    assert np.allclose(grad, expected), "L2 gradient incorrect"
    
    print("✓ l2_gradient passed")


def test_weight_decay():
    """Test weight decay"""
    print("Testing weight_decay...")
    
    weights = np.array([[1.0, 2.0], [3.0, 4.0]])
    decayed = weight_decay(weights, learning_rate=0.1, decay_rate=0.01)
    
    expected = weights * (1 - 0.1 * 0.01)
    assert np.allclose(decayed, expected), "Weight decay incorrect"
    
    print("✓ weight_decay passed")


def test_elastic_net_regularization():
    """Test elastic net regularization"""
    print("Testing elastic_net_regularization...")
    
    weights = np.array([[1.0, -2.0], [3.0, -4.0]])
    penalty = elastic_net_regularization(weights, lambda_=0.01, alpha=0.5)
    
    l1_term = 0.5 * l1_regularization(weights, 0.01)
    l2_term = 0.5 * l2_regularization(weights, 0.01)
    expected = l1_term + l2_term
    
    assert np.isclose(penalty, expected), "Elastic net penalty incorrect"
    
    print("✓ elastic_net_regularization passed")


def test_elastic_net_gradient():
    """Test elastic net gradient"""
    print("Testing elastic_net_gradient...")
    
    weights = np.array([[1.0, -2.0], [3.0, -4.0]])
    grad = elastic_net_gradient(weights, lambda_=0.01, alpha=0.5)
    
    l1_grad = 0.5 * l1_gradient(weights, 0.01)
    l2_grad = 0.5 * l2_gradient(weights, 0.01)
    expected = l1_grad + l2_grad
    
    assert np.allclose(grad, expected), "Elastic net gradient incorrect"
    
    print("✓ elastic_net_gradient passed")


def test_early_stopping_class():
    """Test EarlyStopping class"""
    print("Testing EarlyStopping class...")
    
    early_stopping = EarlyStopping(patience=3, min_delta=0.001, mode='min')
    
    # Simulate training with improving loss
    losses = [1.0, 0.9, 0.8, 0.7, 0.6]
    for loss in losses:
        should_stop = early_stopping(loss)
        assert not should_stop, "Should not stop when improving"
    
    # Simulate no improvement
    early_stopping.reset()
    losses = [1.0, 0.9, 0.91, 0.92, 0.93, 0.94]
    stopped = False
    for i, loss in enumerate(losses):
        should_stop = early_stopping(loss)
        if should_stop:
            stopped = True
            assert i >= 3, "Should stop after patience epochs"
            break
    
    assert stopped, "Should have stopped"
    
    print("✓ EarlyStopping class passed")


def test_early_stopping_monitor():
    """Test early stopping monitor function"""
    print("Testing early_stopping_monitor...")
    
    # Improving losses
    val_losses = [1.0, 0.9, 0.8, 0.7, 0.6]
    should_stop = early_stopping_monitor(val_losses, patience=3)
    assert not should_stop, "Should not stop when improving"
    
    # No improvement
    val_losses = [1.0, 0.9, 0.8, 0.85, 0.86, 0.87, 0.88]
    should_stop = early_stopping_monitor(val_losses, patience=3)
    assert should_stop, "Should stop when not improving"
    
    print("✓ early_stopping_monitor passed")


def test_apply_regularization():
    """Test apply_regularization utility"""
    print("Testing apply_regularization...")
    
    weights = np.random.randn(10, 10)
    
    # Test L1
    penalty_l1 = apply_regularization(weights, reg_type='l1', lambda_=0.01)
    expected_l1 = l1_regularization(weights, 0.01)
    assert np.isclose(penalty_l1, expected_l1), "L1 regularization incorrect"
    
    # Test L2
    penalty_l2 = apply_regularization(weights, reg_type='l2', lambda_=0.01)
    expected_l2 = l2_regularization(weights, 0.01)
    assert np.isclose(penalty_l2, expected_l2), "L2 regularization incorrect"
    
    # Test Elastic Net
    penalty_en = apply_regularization(weights, reg_type='elastic_net', lambda_=0.01, alpha=0.5)
    expected_en = elastic_net_regularization(weights, 0.01, 0.5)
    assert np.isclose(penalty_en, expected_en), "Elastic net regularization incorrect"
    
    print("✓ apply_regularization passed")


def test_compute_regularization_gradient():
    """Test compute_regularization_gradient utility"""
    print("Testing compute_regularization_gradient...")
    
    weights = np.random.randn(10, 10)
    
    # Test L1
    grad_l1 = compute_regularization_gradient(weights, reg_type='l1', lambda_=0.01)
    expected_l1 = l1_gradient(weights, 0.01)
    assert np.allclose(grad_l1, expected_l1), "L1 gradient incorrect"
    
    # Test L2
    grad_l2 = compute_regularization_gradient(weights, reg_type='l2', lambda_=0.01)
    expected_l2 = l2_gradient(weights, 0.01)
    assert np.allclose(grad_l2, expected_l2), "L2 gradient incorrect"
    
    print("✓ compute_regularization_gradient passed")


def test_get_dropout_rate_schedule():
    """Test dropout rate schedule generation"""
    print("Testing get_dropout_rate_schedule...")
    
    # Linear schedule
    rates = get_dropout_rate_schedule(0.5, 0.1, 100, 'linear')
    assert len(rates) == 100, "Schedule length incorrect"
    assert np.isclose(rates[0], 0.5), "Initial rate incorrect"
    assert np.isclose(rates[-1], 0.1), "Final rate incorrect"
    
    # Exponential schedule
    rates = get_dropout_rate_schedule(0.5, 0.1, 100, 'exponential')
    assert len(rates) == 100, "Schedule length incorrect"
    assert rates[0] > rates[-1], "Rates should decrease"
    
    # Cosine schedule
    rates = get_dropout_rate_schedule(0.5, 0.1, 100, 'cosine')
    assert len(rates) == 100, "Schedule length incorrect"
    
    print("✓ get_dropout_rate_schedule passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    x = np.random.randn(32, 128)
    
    # Test inverted_dropout alias
    out1, mask1 = inverted_dropout(x, dropout_rate=0.5, training=True, seed=42)
    out2, mask2 = dropout(x, dropout_rate=0.5, training=True, seed=42)
    assert np.allclose(out1, out2), "inverted_dropout alias should work"
    
    # Test dropout_mask alias
    out3, mask3 = dropout_mask(x, dropout_rate=0.5, training=True, seed=42)
    assert np.allclose(out3, out2), "dropout_mask alias should work"
    
    # Test l1_penalty alias
    weights = np.random.randn(10, 10)
    grad1 = l1_penalty(weights, lambda_=0.01)
    grad2 = l1_gradient(weights, lambda_=0.01)
    assert np.allclose(grad1, grad2), "l1_penalty alias should work"
    
    # Test l2_penalty alias
    grad1 = l2_penalty(weights, lambda_=0.01)
    grad2 = l2_gradient(weights, lambda_=0.01)
    assert np.allclose(grad1, grad2), "l2_penalty alias should work"
    
    print("✓ aliases passed")


def test_dropout_zero_rate():
    """Test dropout with zero rate"""
    print("Testing dropout with zero rate...")
    
    x = np.random.randn(32, 128)
    output, mask = dropout(x, dropout_rate=0.0, training=True)
    
    assert np.array_equal(output, x), "Zero dropout rate should not modify input"
    assert np.all(mask == 1), "Mask should be all ones with zero dropout"
    
    print("✓ dropout with zero rate passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("DROPOUT AND REGULARIZATION MODULE TESTS")
    print("="*60 + "\n")
    
    # Dropout tests
    test_dropout_training()
    test_dropout_inference()
    test_spatial_dropout()
    test_variational_dropout()
    test_dropconnect()
    test_dropout_zero_rate()
    
    # L1 Regularization tests
    test_l1_regularization()
    test_l1_gradient()
    
    # L2 Regularization tests
    test_l2_regularization()
    test_l2_gradient()
    test_weight_decay()
    
    # Elastic Net tests
    test_elastic_net_regularization()
    test_elastic_net_gradient()
    
    # Early Stopping tests
    test_early_stopping_class()
    test_early_stopping_monitor()
    
    # Utility tests
    test_apply_regularization()
    test_compute_regularization_gradient()
    test_get_dropout_rate_schedule()
    
    # Aliases
    test_aliases()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
