"""
Comprehensive tests for weight initialization techniques

Tests all initialization implementations to ensure correctness
and proper functionality.
"""

import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.weight_init import (
    # Xavier/Glorot
    xavier_uniform,
    xavier_normal,
    glorot_uniform,
    glorot_normal,
    # He/Kaiming
    he_uniform,
    he_normal,
    kaiming_uniform,
    kaiming_normal,
    # LeCun
    lecun_uniform,
    lecun_normal,
    # Advanced
    orthogonal,
    identity,
    sparse,
    variance_scaling,
    # Simple
    constant,
    uniform,
    normal,
    # Utilities
    calculate_gain,
    get_initializer,
    WeightInitializer,
)


def test_xavier_uniform():
    """Test Xavier Uniform Initialization"""
    print("Testing Xavier Uniform Initialization...")
    
    shape = (100, 50)
    weights = xavier_uniform(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance (approximately 2/(fan_in + fan_out))
    expected_var = 2.0 / (100 + 50)
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ Xavier Uniform tests passed")


def test_xavier_normal():
    """Test Xavier Normal Initialization"""
    print("Testing Xavier Normal Initialization...")
    
    shape = (100, 50)
    weights = xavier_normal(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance
    expected_var = 2.0 / (100 + 50)
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ Xavier Normal tests passed")


def test_he_uniform():
    """Test He Uniform Initialization"""
    print("Testing He Uniform Initialization...")
    
    shape = (100, 50)
    weights = he_uniform(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance (approximately 2/fan_in)
    expected_var = 2.0 / 100
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ He Uniform tests passed")


def test_he_normal():
    """Test He Normal Initialization"""
    print("Testing He Normal Initialization...")
    
    shape = (100, 50)
    weights = he_normal(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance
    expected_var = 2.0 / 100
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ He Normal tests passed")


def test_lecun_uniform():
    """Test LeCun Uniform Initialization"""
    print("Testing LeCun Uniform Initialization...")
    
    shape = (100, 50)
    weights = lecun_uniform(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance (approximately 1/fan_in)
    expected_var = 1.0 / 100
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ LeCun Uniform tests passed")


def test_lecun_normal():
    """Test LeCun Normal Initialization"""
    print("Testing LeCun Normal Initialization...")
    
    shape = (100, 50)
    weights = lecun_normal(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test variance
    expected_var = 1.0 / 100
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        f"Variance mismatch: expected {expected_var}, got {actual_var}"
    
    # Test mean close to zero
    assert np.abs(np.mean(weights)) < 0.1, "Mean should be close to zero"
    
    print("✓ LeCun Normal tests passed")


def test_orthogonal():
    """Test Orthogonal Initialization"""
    print("Testing Orthogonal Initialization...")
    
    shape = (50, 50)
    weights = orthogonal(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test orthogonality (W @ W.T should be close to identity)
    product = np.dot(weights, weights.T)
    identity_matrix = np.eye(shape[0])
    assert np.allclose(product, identity_matrix, atol=1e-5), \
        "Matrix should be orthogonal"
    
    print("✓ Orthogonal tests passed")


def test_identity():
    """Test Identity Initialization"""
    print("Testing Identity Initialization...")
    
    shape = (50, 50)
    weights = identity(shape)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test identity
    expected = np.eye(50)
    assert np.allclose(weights, expected), "Should be identity matrix"
    
    # Test with gain
    weights_scaled = identity(shape, gain=2.0)
    expected_scaled = np.eye(50) * 2.0
    assert np.allclose(weights_scaled, expected_scaled), \
        "Scaled identity incorrect"
    
    print("✓ Identity tests passed")


def test_sparse():
    """Test Sparse Initialization"""
    print("Testing Sparse Initialization...")
    
    shape = (100, 100)
    sparsity = 0.5
    weights = sparse(shape, sparsity=sparsity)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test sparsity
    zero_fraction = np.sum(weights == 0) / weights.size
    assert np.isclose(zero_fraction, sparsity, atol=0.1), \
        f"Sparsity mismatch: expected {sparsity}, got {zero_fraction}"
    
    print("✓ Sparse tests passed")


def test_variance_scaling():
    """Test Variance Scaling Initialization"""
    print("Testing Variance Scaling Initialization...")
    
    shape = (100, 50)
    
    # Test fan_in mode
    weights = variance_scaling(shape, scale=2.0, mode='fan_in')
    expected_var = 2.0 / 100
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        "fan_in variance incorrect"
    
    # Test fan_out mode
    weights = variance_scaling(shape, scale=2.0, mode='fan_out')
    expected_var = 2.0 / 50
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        "fan_out variance incorrect"
    
    # Test fan_avg mode
    weights = variance_scaling(shape, scale=2.0, mode='fan_avg')
    expected_var = 2.0 / 75
    actual_var = np.var(weights)
    assert np.isclose(actual_var, expected_var, rtol=0.3), \
        "fan_avg variance incorrect"
    
    print("✓ Variance Scaling tests passed")


def test_constant():
    """Test Constant Initialization"""
    print("Testing Constant Initialization...")
    
    shape = (10, 10)
    value = 0.5
    weights = constant(shape, value=value)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test all values are constant
    assert np.all(weights == value), "All values should be constant"
    
    print("✓ Constant tests passed")


def test_uniform():
    """Test Uniform Initialization"""
    print("Testing Uniform Initialization...")
    
    shape = (100, 100)
    low, high = -0.1, 0.1
    weights = uniform(shape, low=low, high=high)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test bounds
    assert np.all(weights >= low) and np.all(weights <= high), \
        "Values should be within bounds"
    
    # Test approximately uniform distribution
    mean = (low + high) / 2
    assert np.abs(np.mean(weights) - mean) < 0.05, \
        "Mean should be close to midpoint"
    
    print("✓ Uniform tests passed")


def test_normal():
    """Test Normal Initialization"""
    print("Testing Normal Initialization...")
    
    shape = (100, 100)
    mean, std = 0.0, 0.1
    weights = normal(shape, mean=mean, std=std)
    
    # Test shape
    assert weights.shape == shape, "Shape mismatch"
    
    # Test mean
    assert np.abs(np.mean(weights) - mean) < 0.05, \
        "Mean should be close to specified value"
    
    # Test std
    assert np.abs(np.std(weights) - std) < 0.05, \
        "Std should be close to specified value"
    
    print("✓ Normal tests passed")


def test_calculate_gain():
    """Test calculate_gain function"""
    print("Testing calculate_gain...")
    
    # Test known gains
    assert calculate_gain('linear') == 1.0
    assert calculate_gain('sigmoid') == 1.0
    assert np.isclose(calculate_gain('tanh'), 5.0/3.0)
    assert np.isclose(calculate_gain('relu'), np.sqrt(2.0))
    
    # Test invalid activation
    try:
        calculate_gain('invalid')
        assert False, "Should raise error for invalid activation"
    except ValueError:
        pass
    
    print("✓ calculate_gain tests passed")


def test_get_initializer():
    """Test get_initializer factory function"""
    print("Testing get_initializer...")
    
    shape = (10, 10)
    
    # Test creating different initializers
    methods = [
        'xavier_uniform',
        'xavier_normal',
        'he_uniform',
        'he_normal',
        'lecun_uniform',
        'lecun_normal',
        'orthogonal',
        'constant',
    ]
    
    for method in methods:
        weights = get_initializer(method, shape)
        assert weights.shape == shape, f"{method} shape mismatch"
    
    # Test invalid method
    try:
        get_initializer('invalid', shape)
        assert False, "Should raise error for invalid method"
    except ValueError:
        pass
    
    print("✓ get_initializer tests passed")


def test_weight_initializer_class():
    """Test WeightInitializer class"""
    print("Testing WeightInitializer class...")
    
    shape = (10, 10)
    
    # Test initialization
    initializer = WeightInitializer('xavier_normal')
    weights = initializer.initialize(shape)
    assert weights.shape == shape, "Shape mismatch"
    
    # Test callable
    weights2 = initializer(shape)
    assert weights2.shape == shape, "Callable shape mismatch"
    
    # Test with parameters
    initializer = WeightInitializer('constant', value=0.5)
    weights = initializer(shape)
    assert np.all(weights == 0.5), "Constant value incorrect"
    
    print("✓ WeightInitializer class tests passed")


def test_aliases():
    """Test that aliases work correctly"""
    print("Testing aliases...")
    
    # Test Glorot aliases
    assert glorot_uniform == xavier_uniform
    assert glorot_normal == xavier_normal
    
    # Test Kaiming aliases
    assert kaiming_uniform == he_uniform
    assert kaiming_normal == he_normal
    
    print("✓ Aliases tests passed")


def test_convolutional_shapes():
    """Test initialization with convolutional layer shapes"""
    print("Testing convolutional shapes...")
    
    # Conv2D shape: (out_channels, in_channels, kernel_h, kernel_w)
    shape = (64, 32, 3, 3)
    
    # Test Xavier
    weights = xavier_normal(shape)
    assert weights.shape == shape, "Conv shape mismatch"
    
    # Test He
    weights = he_normal(shape)
    assert weights.shape == shape, "Conv shape mismatch"
    
    print("✓ Convolutional shapes tests passed")


def test_integration_neural_network():
    """Test integration with simulated neural network"""
    print("Testing integration with neural network...")
    
    # Simulate a simple 3-layer network
    layer_sizes = [(784, 256), (256, 128), (128, 10)]
    
    # Initialize all layers with He initialization (for ReLU)
    weights = []
    for shape in layer_sizes:
        w = he_normal(shape)
        weights.append(w)
        
        # Check variance is appropriate
        fan_in = shape[0]
        expected_var = 2.0 / fan_in
        actual_var = np.var(w)
        assert np.isclose(actual_var, expected_var, rtol=0.3), \
            f"Layer {shape} variance incorrect"
    
    # Simulate forward pass
    x = np.random.randn(32, 784)  # Batch of 32
    
    for w in weights:
        x = np.dot(x, w)
        x = np.maximum(0, x)  # ReLU
    
    # Check output is reasonable
    assert not np.any(np.isnan(x)), "Forward pass produced NaN"
    assert not np.any(np.isinf(x)), "Forward pass produced Inf"
    
    print("✓ Integration with neural network tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("WEIGHT INITIALIZATION - COMPREHENSIVE TESTS")
    print("=" * 70)
    print()
    
    tests = [
        test_xavier_uniform,
        test_xavier_normal,
        test_he_uniform,
        test_he_normal,
        test_lecun_uniform,
        test_lecun_normal,
        test_orthogonal,
        test_identity,
        test_sparse,
        test_variance_scaling,
        test_constant,
        test_uniform,
        test_normal,
        test_calculate_gain,
        test_get_initializer,
        test_weight_initializer_class,
        test_aliases,
        test_convolutional_shapes,
        test_integration_neural_network,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed_tests.append(test.__name__)
    
    print()
    print("=" * 70)
    if not failed_tests:
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  Total tests: {len(tests)}")
        print(f"  Passed: {len(tests)}")
        print(f"  Failed: 0")
        print()
        print("All weight initialization techniques are working correctly!")
        return 0
    else:
        print("SOME TESTS FAILED! ✗")
        print("=" * 70)
        print()
        print("Failed tests:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print()
        print(f"Summary:")
        print(f"  Total tests: {len(tests)}")
        print(f"  Passed: {len(tests) - len(failed_tests)}")
        print(f"  Failed: {len(failed_tests)}")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
