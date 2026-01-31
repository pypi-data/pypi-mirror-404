"""
Tests for advanced normalization techniques module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.normalization_advanced import (
    # Batch Normalization
    batch_norm_forward,
    # Layer Normalization
    layer_norm_forward,
    # Instance Normalization
    instance_norm_forward,
    # Group Normalization
    group_norm_forward,
    # Weight Normalization
    weight_norm,
    # Spectral Normalization
    spectral_norm,
    # Utilities
    initialize_norm_params,
    compute_norm_stats,
    # Aliases
    batch_norm,
    layer_norm,
    instance_norm,
    group_norm,
)


def test_batch_norm_training():
    """Test batch normalization in training mode"""
    print("Testing batch_norm_forward (training)...")
    
    # Test with 4D input (CNN)
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    output, running_mean, running_var = batch_norm_forward(
        x, gamma, beta, training=True
    )
    
    assert output.shape == x.shape, "Output shape should match input"
    assert running_mean.shape == (64,), "Running mean shape incorrect"
    assert running_var.shape == (64,), "Running var shape incorrect"
    
    # Check normalization (approximately zero mean, unit variance)
    output_mean = np.mean(output, axis=(0, 2, 3))
    output_var = np.var(output, axis=(0, 2, 3))
    assert np.allclose(output_mean, 0, atol=1e-5), "Mean should be close to 0"
    assert np.allclose(output_var, 1, atol=0.1), "Variance should be close to 1"
    
    print("✓ batch_norm_forward (training) passed")


def test_batch_norm_inference():
    """Test batch normalization in inference mode"""
    print("Testing batch_norm_forward (inference)...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    running_mean = np.zeros(64)
    running_var = np.ones(64)
    
    output, _, _ = batch_norm_forward(
        x, gamma, beta, running_mean, running_var, training=False
    )
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ batch_norm_forward (inference) passed")


def test_batch_norm_fc():
    """Test batch normalization with fully connected layers"""
    print("Testing batch_norm_forward (FC)...")
    
    x = np.random.randn(32, 256)
    gamma, beta = initialize_norm_params(256)
    
    output, running_mean, running_var = batch_norm_forward(
        x, gamma, beta, training=True
    )
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization
    output_mean = np.mean(output, axis=0)
    output_var = np.var(output, axis=0)
    assert np.allclose(output_mean, 0, atol=1e-5), "Mean should be close to 0"
    assert np.allclose(output_var, 1, atol=0.1), "Variance should be close to 1"
    
    print("✓ batch_norm_forward (FC) passed")


def test_layer_norm_2d():
    """Test layer normalization with 2D input"""
    print("Testing layer_norm_forward (2D)...")
    
    x = np.random.randn(32, 256)
    gamma, beta = initialize_norm_params(256)
    
    output = layer_norm_forward(x, gamma, beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per sample
    for i in range(x.shape[0]):
        sample_mean = np.mean(output[i])
        sample_var = np.var(output[i])
        assert np.isclose(sample_mean, 0, atol=1e-5), f"Sample {i} mean should be 0"
        assert np.isclose(sample_var, 1, atol=0.1), f"Sample {i} variance should be 1"
    
    print("✓ layer_norm_forward (2D) passed")


def test_layer_norm_3d():
    """Test layer normalization with 3D input (Transformers)"""
    print("Testing layer_norm_forward (3D)...")
    
    x = np.random.randn(32, 10, 512)  # (batch, seq_len, features)
    gamma, beta = initialize_norm_params(512)
    
    output = layer_norm_forward(x, gamma, beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per sample, per timestep
    for i in range(x.shape[0]):
        for t in range(x.shape[1]):
            sample_mean = np.mean(output[i, t])
            sample_var = np.var(output[i, t])
            assert np.isclose(sample_mean, 0, atol=1e-5), "Mean should be 0"
            assert np.isclose(sample_var, 1, atol=0.1), "Variance should be 1"
    
    print("✓ layer_norm_forward (3D) passed")


def test_instance_norm():
    """Test instance normalization"""
    print("Testing instance_norm_forward...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    output = instance_norm_forward(x, gamma, beta)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    # Check normalization per instance, per channel
    for i in range(x.shape[0]):
        for c in range(x.shape[1]):
            channel_mean = np.mean(output[i, c])
            channel_var = np.var(output[i, c])
            assert np.isclose(channel_mean, 0, atol=1e-5), "Mean should be 0"
            assert np.isclose(channel_var, 1, atol=0.1), "Variance should be 1"
    
    print("✓ instance_norm_forward passed")


def test_group_norm():
    """Test group normalization"""
    print("Testing group_norm_forward...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    output = group_norm_forward(x, gamma, beta, num_groups=32)
    
    assert output.shape == x.shape, "Output shape should match input"
    
    print("✓ group_norm_forward passed")


def test_group_norm_invalid_groups():
    """Test group normalization with invalid number of groups"""
    print("Testing group_norm_forward with invalid groups...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    try:
        output = group_norm_forward(x, gamma, beta, num_groups=7)  # 64 not divisible by 7
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "divisible" in str(e).lower()
    
    print("✓ group_norm_forward invalid groups passed")


def test_weight_norm():
    """Test weight normalization"""
    print("Testing weight_norm...")
    
    weight = np.random.randn(64, 128)
    
    w_normalized, g = weight_norm(weight, dim=1)
    
    assert w_normalized.shape == weight.shape, "Normalized weight shape should match"
    assert g.shape == (64, 1), "Norm shape incorrect"
    
    # Check that each row has unit norm
    row_norms = np.linalg.norm(w_normalized, axis=1)
    assert np.allclose(row_norms, 1.0), "Each row should have unit norm"
    
    print("✓ weight_norm passed")


def test_spectral_norm():
    """Test spectral normalization"""
    print("Testing spectral_norm...")
    
    weight = np.random.randn(64, 128)
    
    w_normalized = spectral_norm(weight, num_iterations=1)
    
    assert w_normalized.shape == weight.shape, "Normalized weight shape should match"
    
    # Check that largest singular value is approximately 1
    u, s, v = np.linalg.svd(w_normalized, full_matrices=False)
    assert np.isclose(s[0], 1.0, atol=0.1), "Largest singular value should be close to 1"
    
    print("✓ spectral_norm passed")


def test_initialize_norm_params():
    """Test normalization parameter initialization"""
    print("Testing initialize_norm_params...")
    
    gamma, beta = initialize_norm_params(256)
    
    assert gamma.shape == (256,), "Gamma shape incorrect"
    assert beta.shape == (256,), "Beta shape incorrect"
    assert np.allclose(gamma, 1.0), "Gamma should be initialized to 1"
    assert np.allclose(beta, 0.0), "Beta should be initialized to 0"
    
    print("✓ initialize_norm_params passed")


def test_compute_norm_stats():
    """Test normalization statistics computation"""
    print("Testing compute_norm_stats...")
    
    x = np.random.randn(32, 64, 28, 28)
    
    # Batch norm stats
    mean, var = compute_norm_stats(x, norm_type='batch')
    assert mean.shape == (1, 64, 1, 1), "Batch norm mean shape incorrect"
    assert var.shape == (1, 64, 1, 1), "Batch norm var shape incorrect"
    
    # Layer norm stats
    mean, var = compute_norm_stats(x, norm_type='layer')
    assert mean.shape == (32, 64, 28, 1), "Layer norm mean shape incorrect"
    
    # Instance norm stats
    mean, var = compute_norm_stats(x, norm_type='instance')
    assert mean.shape == (32, 64, 1, 1), "Instance norm mean shape incorrect"
    
    print("✓ compute_norm_stats passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    # Test batch_norm alias
    out1, _, _ = batch_norm(x, gamma, beta, training=True)
    out2, _, _ = batch_norm_forward(x, gamma, beta, training=True)
    assert np.allclose(out1, out2), "batch_norm alias should work"
    
    # Test layer_norm alias
    x_2d = np.random.randn(32, 256)
    gamma_2d, beta_2d = initialize_norm_params(256)
    out1 = layer_norm(x_2d, gamma_2d, beta_2d)
    out2 = layer_norm_forward(x_2d, gamma_2d, beta_2d)
    assert np.allclose(out1, out2), "layer_norm alias should work"
    
    print("✓ aliases passed")


def test_batch_norm_running_stats():
    """Test batch normalization running statistics update"""
    print("Testing batch_norm running statistics...")
    
    x = np.random.randn(32, 64, 28, 28)
    gamma, beta = initialize_norm_params(64)
    
    running_mean = np.zeros(64)
    running_var = np.ones(64)
    
    # First forward pass
    _, running_mean_1, running_var_1 = batch_norm_forward(
        x, gamma, beta, running_mean, running_var, momentum=0.9, training=True
    )
    
    # Check that running stats were updated
    assert not np.allclose(running_mean_1, running_mean), "Running mean should be updated"
    assert not np.allclose(running_var_1, running_var), "Running var should be updated"
    
    print("✓ batch_norm running statistics passed")


def test_normalization_with_scale_shift():
    """Test that scale and shift parameters work correctly"""
    print("Testing normalization with scale and shift...")
    
    x = np.random.randn(32, 256)
    
    # Custom gamma and beta
    gamma = np.ones(256) * 2.0  # Scale by 2
    beta = np.ones(256) * 3.0   # Shift by 3
    
    output = layer_norm_forward(x, gamma, beta)
    
    # After normalization, mean should be close to beta, std close to gamma
    output_mean = np.mean(output, axis=0)
    assert np.allclose(output_mean, 3.0, atol=0.1), "Mean should be close to beta"
    
    print("✓ normalization with scale and shift passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADVANCED NORMALIZATION TECHNIQUES MODULE TESTS")
    print("="*60 + "\n")
    
    # Batch Normalization tests
    test_batch_norm_training()
    test_batch_norm_inference()
    test_batch_norm_fc()
    test_batch_norm_running_stats()
    
    # Layer Normalization tests
    test_layer_norm_2d()
    test_layer_norm_3d()
    
    # Instance Normalization tests
    test_instance_norm()
    
    # Group Normalization tests
    test_group_norm()
    test_group_norm_invalid_groups()
    
    # Weight Normalization tests
    test_weight_norm()
    
    # Spectral Normalization tests
    test_spectral_norm()
    
    # Utility tests
    test_initialize_norm_params()
    test_compute_norm_stats()
    
    # Aliases
    test_aliases()
    
    # Additional tests
    test_normalization_with_scale_shift()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
