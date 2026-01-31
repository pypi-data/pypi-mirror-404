"""
Tests for Batch Normalization and Layer Normalization
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.normalization import (
    # Classes
    BatchNorm1d,
    BatchNorm2d,
    LayerNorm,
    GroupNorm,
    InstanceNorm,
    # Functional API
    batch_norm_1d,
    layer_norm,
    group_norm,
    instance_norm,
    # Aliases
    batchnorm1d,
    layernorm,
    groupnorm,
    instancenorm,
)


def test_batchnorm1d_training():
    """Test BatchNorm1d in training mode"""
    print("Testing BatchNorm1d (training)...")
    
    bn = BatchNorm1d(num_features=128)
    x = np.random.randn(32, 128)
    
    output = bn.forward(x, training=True)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization (mean ≈ 0, var ≈ 1)
    output_mean = np.mean(output, axis=0)
    output_var = np.var(output, axis=0)
    
    assert np.allclose(output_mean, 0, atol=1e-6), "Mean should be close to 0"
    assert np.allclose(output_var, 1, atol=1e-1), "Variance should be close to 1"
    
    # Check running statistics updated
    assert bn.num_batches_tracked == 1, "Should track batch count"
    
    print("✓ BatchNorm1d (training) passed")


def test_batchnorm1d_inference():
    """Test BatchNorm1d in inference mode"""
    print("Testing BatchNorm1d (inference)...")
    
    bn = BatchNorm1d(num_features=128)
    
    # Train on some batches
    for _ in range(10):
        x_train = np.random.randn(32, 128)
        bn.forward(x_train, training=True)
    
    # Test inference
    x_test = np.random.randn(1, 128)
    output = bn.forward(x_test, training=False)
    
    assert output.shape == x_test.shape, "Output shape should match input"
    assert bn.num_batches_tracked == 10, "Should have tracked 10 batches"
    
    print("✓ BatchNorm1d (inference) passed")


def test_batchnorm1d_backward():
    """Test BatchNorm1d backward pass"""
    print("Testing BatchNorm1d backward...")
    
    bn = BatchNorm1d(num_features=128)
    x = np.random.randn(32, 128)
    
    # Forward
    output = bn.forward(x, training=True)
    
    # Backward
    grad_output = np.random.randn(*output.shape)
    grad_input, grads = bn.backward(grad_output)
    
    assert grad_input.shape == x.shape, "Gradient shape should match input"
    assert grads['gamma'].shape == (128,), "Gamma gradient shape incorrect"
    assert grads['beta'].shape == (128,), "Beta gradient shape incorrect"
    
    print("✓ BatchNorm1d backward passed")


def test_batchnorm2d_training():
    """Test BatchNorm2d for CNNs"""
    print("Testing BatchNorm2d...")
    
    bn = BatchNorm2d(num_features=64)
    x = np.random.randn(32, 64, 28, 28)
    
    output = bn.forward(x, training=True)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per channel
    for c in range(64):
        channel_data = output[:, c, :, :]
        channel_mean = np.mean(channel_data)
        channel_var = np.var(channel_data)
        
        assert np.abs(channel_mean) < 1e-5, f"Channel {c} mean should be close to 0"
        assert np.abs(channel_var - 1) < 0.2, f"Channel {c} variance should be close to 1"
    
    print("✓ BatchNorm2d passed")


def test_layernorm():
    """Test LayerNorm"""
    print("Testing LayerNorm...")
    
    ln = LayerNorm(normalized_shape=512)
    x = np.random.randn(32, 10, 512)
    
    output = ln.forward(x)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per sample
    for i in range(32):
        for j in range(10):
            sample_data = output[i, j, :]
            sample_mean = np.mean(sample_data)
            sample_var = np.var(sample_data)
            
            assert np.abs(sample_mean) < 1e-5, f"Sample ({i},{j}) mean should be close to 0"
            assert np.abs(sample_var - 1) < 0.1, f"Sample ({i},{j}) variance should be close to 1"
    
    print("✓ LayerNorm passed")


def test_layernorm_backward():
    """Test LayerNorm backward pass"""
    print("Testing LayerNorm backward...")
    
    ln = LayerNorm(normalized_shape=512)
    x = np.random.randn(32, 10, 512)
    
    # Forward
    output = ln.forward(x)
    
    # Backward
    grad_output = np.random.randn(*output.shape)
    grad_input, grads = ln.backward(grad_output)
    
    assert grad_input.shape == x.shape, "Gradient shape should match input"
    assert grads['gamma'].shape == (512,), "Gamma gradient shape incorrect"
    assert grads['beta'].shape == (512,), "Beta gradient shape incorrect"
    
    print("✓ LayerNorm backward passed")


def test_groupnorm():
    """Test GroupNorm"""
    print("Testing GroupNorm...")
    
    gn = GroupNorm(num_groups=8, num_channels=64)
    x = np.random.randn(32, 64, 28, 28)
    
    output = gn.forward(x)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ GroupNorm passed")


def test_instancenorm():
    """Test InstanceNorm"""
    print("Testing InstanceNorm...")
    
    in_norm = InstanceNorm(num_features=64)
    x = np.random.randn(32, 64, 28, 28)
    
    output = in_norm.forward(x)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per instance and channel
    for n in range(32):
        for c in range(64):
            instance_data = output[n, c, :, :]
            instance_mean = np.mean(instance_data)
            instance_var = np.var(instance_data)
            
            assert np.abs(instance_mean) < 1e-5, f"Instance ({n},{c}) mean should be close to 0"
            assert np.abs(instance_var - 1) < 0.2, f"Instance ({n},{c}) variance should be close to 1"
    
    print("✓ InstanceNorm passed")


def test_functional_batch_norm():
    """Test functional batch_norm_1d"""
    print("Testing functional batch_norm_1d...")
    
    x = np.random.randn(32, 128)
    gamma = np.ones(128)
    beta = np.zeros(128)
    running_mean = np.zeros(128)
    running_var = np.ones(128)
    
    output, new_mean, new_var = batch_norm_1d(
        x, gamma, beta, running_mean, running_var, training=True
    )
    
    assert output.shape == x.shape, "Output shape should match input"
    assert new_mean is not None, "Running mean should be updated"
    assert new_var is not None, "Running var should be updated"
    
    print("✓ functional batch_norm_1d passed")


def test_functional_layer_norm():
    """Test functional layer_norm"""
    print("Testing functional layer_norm...")
    
    x = np.random.randn(32, 10, 512)
    gamma = np.ones(512)
    beta = np.zeros(512)
    
    output = layer_norm(x, gamma, beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ functional layer_norm passed")


def test_functional_group_norm():
    """Test functional group_norm"""
    print("Testing functional group_norm...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    output = group_norm(x, num_groups=8, gamma=gamma, beta=beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ functional group_norm passed")


def test_functional_instance_norm():
    """Test functional instance_norm"""
    print("Testing functional instance_norm...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    output = instance_norm(x, gamma, beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ functional instance_norm passed")


def test_batchnorm_reset_stats():
    """Test resetting running statistics"""
    print("Testing reset_running_stats...")
    
    bn = BatchNorm1d(num_features=128)
    
    # Train on some batches
    for _ in range(5):
        x = np.random.randn(32, 128)
        bn.forward(x, training=True)
    
    assert bn.num_batches_tracked == 5, "Should have tracked 5 batches"
    
    # Reset
    bn.reset_running_stats()
    
    assert bn.num_batches_tracked == 0, "Batch count should be reset"
    assert np.allclose(bn.running_mean, 0), "Running mean should be reset"
    assert np.allclose(bn.running_var, 1), "Running var should be reset"
    
    print("✓ reset_running_stats passed")


def test_batchnorm_no_affine():
    """Test BatchNorm without affine parameters"""
    print("Testing BatchNorm without affine...")
    
    bn = BatchNorm1d(num_features=128, affine=False)
    x = np.random.randn(32, 128)
    
    output = bn.forward(x, training=True)
    
    assert output.shape == x.shape, "Output shape should match input"
    assert bn.gamma is None, "Gamma should be None"
    assert bn.beta is None, "Beta should be None"
    
    print("✓ BatchNorm without affine passed")


def test_layernorm_no_affine():
    """Test LayerNorm without affine parameters"""
    print("Testing LayerNorm without affine...")
    
    ln = LayerNorm(normalized_shape=512, elementwise_affine=False)
    x = np.random.randn(32, 10, 512)
    
    output = ln.forward(x)
    
    assert output.shape == x.shape, "Output shape should match input"
    assert ln.gamma is None, "Gamma should be None"
    assert ln.beta is None, "Beta should be None"
    
    print("✓ LayerNorm without affine passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    x = np.random.randn(32, 128)
    gamma = np.ones(128)
    beta = np.zeros(128)
    running_mean = np.zeros(128)
    running_var = np.ones(128)
    
    # Test batchnorm1d alias
    out1, _, _ = batchnorm1d(x, gamma, beta, running_mean, running_var, training=True)
    out2, _, _ = batch_norm_1d(x, gamma, beta, running_mean, running_var, training=True)
    assert np.allclose(out1, out2), "batchnorm1d alias should work"
    
    # Test layernorm alias
    x_ln = np.random.randn(32, 10, 512)
    gamma_ln = np.ones(512)
    beta_ln = np.zeros(512)
    
    out1 = layernorm(x_ln, gamma_ln, beta_ln)
    out2 = layer_norm(x_ln, gamma_ln, beta_ln)
    assert np.allclose(out1, out2), "layernorm alias should work"
    
    print("✓ aliases passed")


def test_batchnorm_3d_input():
    """Test BatchNorm1d with 3D input"""
    print("Testing BatchNorm1d with 3D input...")
    
    bn = BatchNorm1d(num_features=128)
    x = np.random.randn(32, 128, 10)  # (N, C, L)
    
    output = bn.forward(x, training=True)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ BatchNorm1d with 3D input passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("BATCH NORMALIZATION AND LAYER NORMALIZATION TESTS")
    print("="*60 + "\n")
    
    # BatchNorm1d tests
    test_batchnorm1d_training()
    test_batchnorm1d_inference()
    test_batchnorm1d_backward()
    test_batchnorm_3d_input()
    test_batchnorm_no_affine()
    test_batchnorm_reset_stats()
    
    # BatchNorm2d tests
    test_batchnorm2d_training()
    
    # LayerNorm tests
    test_layernorm()
    test_layernorm_backward()
    test_layernorm_no_affine()
    
    # GroupNorm tests
    test_groupnorm()
    
    # InstanceNorm tests
    test_instancenorm()
    
    # Functional API tests
    test_functional_batch_norm()
    test_functional_layer_norm()
    test_functional_group_norm()
    test_functional_instance_norm()
    
    # Aliases
    test_aliases()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
