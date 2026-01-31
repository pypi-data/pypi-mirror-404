"""
Comprehensive Tests for Loss Functions

Tests all loss functions with various scenarios and edge cases.

Author: Ali Mehdi
Date: January 13, 2026
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.losses import (
    MSE,
    MAE,
    HuberLoss,
    CrossEntropy,
    BinaryCrossEntropy,
    FocalLoss,
    DiceLoss,
    HingeLoss,
    KLDivergence,
    CosineSimilarityLoss,
    TripletLoss,
    mse_loss,
    mae_loss,
    huber_loss,
    cross_entropy_loss,
    binary_cross_entropy_loss,
    focal_loss,
    dice_loss,
    hinge_loss,
    kl_divergence_loss,
    cosine_similarity_loss,
    triplet_loss,
)


def test_mse_basic():
    """Test basic MSE functionality."""
    print("Testing MSE basic...")
    
    mse = MSE()
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    
    loss = mse(y_true, y_pred)
    assert np.isclose(loss, 0.0), f"Expected 0.0, got {loss}"
    
    y_pred = np.array([2.0, 3.0, 4.0])
    loss = mse(y_true, y_pred)
    assert np.isclose(loss, 1.0), f"Expected 1.0, got {loss}"
    
    print("✓ MSE basic test passed")


def test_mse_reduction():
    """Test MSE with different reduction modes."""
    print("Testing MSE reduction...")
    
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 3.0, 4.0])
    
    mse_mean = MSE(reduction='mean')
    mse_sum = MSE(reduction='sum')
    mse_none = MSE(reduction='none')
    
    loss_mean = mse_mean(y_true, y_pred)
    loss_sum = mse_sum(y_true, y_pred)
    loss_none = mse_none(y_true, y_pred)
    
    assert np.isclose(loss_mean, 1.0)
    assert np.isclose(loss_sum, 3.0)
    assert loss_none.shape == y_true.shape
    
    print("✓ MSE reduction test passed")


def test_mae_basic():
    """Test basic MAE functionality."""
    print("Testing MAE basic...")
    
    mae = MAE()
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 3.0, 4.0])
    
    loss = mae(y_true, y_pred)
    assert np.isclose(loss, 1.0), f"Expected 1.0, got {loss}"
    
    print("✓ MAE basic test passed")


def test_huber_loss_basic():
    """Test basic Huber loss functionality."""
    print("Testing Huber loss basic...")
    
    huber = HuberLoss(delta=1.0)
    
    # Small error (quadratic)
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    loss = huber(y_true, y_pred)
    assert loss > 0
    
    # Large error (linear)
    y_pred = np.array([5.0, 6.0, 7.0])
    loss_large = huber(y_true, y_pred)
    assert loss_large > loss
    
    print("✓ Huber loss basic test passed")


def test_cross_entropy_basic():
    """Test basic cross entropy functionality."""
    print("Testing cross entropy basic...")
    
    ce = CrossEntropy()
    
    # Perfect prediction
    y_true = np.array([[1, 0, 0], [0, 1, 0]])
    y_pred = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    loss = ce(y_true, y_pred)
    assert loss < 0.01  # Should be very small
    
    # Random prediction
    y_pred = np.array([[0.33, 0.33, 0.34], [0.33, 0.33, 0.34]])
    loss_random = ce(y_true, y_pred)
    assert loss_random > loss
    
    print("✓ Cross entropy basic test passed")


def test_cross_entropy_from_logits():
    """Test cross entropy with logits."""
    print("Testing cross entropy from logits...")
    
    ce = CrossEntropy(from_logits=True)
    
    y_true = np.array([[1, 0, 0], [0, 1, 0]])
    y_logits = np.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    
    loss = ce(y_true, y_logits)
    assert loss > 0
    
    print("✓ Cross entropy from logits test passed")


def test_binary_cross_entropy_basic():
    """Test basic binary cross entropy functionality."""
    print("Testing binary cross entropy basic...")
    
    bce = BinaryCrossEntropy()
    
    # Perfect prediction
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1.0, 0.0, 1.0, 0.0])
    loss = bce(y_true, y_pred)
    assert loss < 0.01
    
    # Random prediction
    y_pred = np.array([0.5, 0.5, 0.5, 0.5])
    loss_random = bce(y_true, y_pred)
    assert loss_random > loss
    
    print("✓ Binary cross entropy basic test passed")


def test_focal_loss_basic():
    """Test basic focal loss functionality."""
    print("Testing focal loss basic...")
    
    focal = FocalLoss(alpha=0.25, gamma=2.0)
    
    y_true = np.array([1, 0, 1, 0])
    
    # Easy examples (high confidence)
    y_pred_easy = np.array([0.9, 0.1, 0.9, 0.1])
    loss_easy = focal(y_true, y_pred_easy)
    
    # Hard examples (low confidence)
    y_pred_hard = np.array([0.6, 0.4, 0.6, 0.4])
    loss_hard = focal(y_true, y_pred_hard)
    
    # Focal loss should focus more on hard examples
    assert loss_hard > loss_easy
    
    print("✓ Focal loss basic test passed")


def test_dice_loss_basic():
    """Test basic Dice loss functionality."""
    print("Testing Dice loss basic...")
    
    dice = DiceLoss()
    
    # Perfect overlap
    y_true = np.array([[1, 1, 0, 0], [0, 1, 1, 0]])
    y_pred = np.array([[1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 1.0, 0.0]])
    loss = dice(y_true, y_pred)
    assert loss < 0.01
    
    # No overlap
    y_pred = np.array([[0.0, 0.0, 1.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
    loss_no_overlap = dice(y_true, y_pred)
    assert loss_no_overlap > 0.9
    
    print("✓ Dice loss basic test passed")


def test_hinge_loss_basic():
    """Test basic hinge loss functionality."""
    print("Testing hinge loss basic...")
    
    hinge = HingeLoss()
    
    # Correct classification with margin
    y_true = np.array([1, -1, 1, -1])
    y_pred = np.array([2.0, -2.0, 2.0, -2.0])
    loss = hinge(y_true, y_pred)
    assert loss < 0.01
    
    # Incorrect classification
    y_pred = np.array([-1.0, 1.0, -1.0, 1.0])
    loss_wrong = hinge(y_true, y_pred)
    assert loss_wrong > 1.0
    
    print("✓ Hinge loss basic test passed")


def test_kl_divergence_basic():
    """Test basic KL divergence functionality."""
    print("Testing KL divergence basic...")
    
    kl = KLDivergence()
    
    # Identical distributions
    y_true = np.array([[0.5, 0.3, 0.2], [0.4, 0.4, 0.2]])
    y_pred = np.array([[0.5, 0.3, 0.2], [0.4, 0.4, 0.2]])
    loss = kl(y_true, y_pred)
    assert loss < 0.01
    
    # Different distributions
    y_pred = np.array([[0.3, 0.5, 0.2], [0.2, 0.4, 0.4]])
    loss_diff = kl(y_true, y_pred)
    assert loss_diff > loss
    
    print("✓ KL divergence basic test passed")


def test_cosine_similarity_loss_basic():
    """Test basic cosine similarity loss functionality."""
    print("Testing cosine similarity loss basic...")
    
    cosine = CosineSimilarityLoss()
    
    # Identical vectors
    y_true = np.array([[1, 2, 3], [4, 5, 6]])
    y_pred = np.array([[1, 2, 3], [4, 5, 6]])
    loss = cosine(y_true, y_pred)
    assert loss < 0.01
    
    # Orthogonal vectors
    y_true = np.array([[1, 0, 0]])
    y_pred = np.array([[0, 1, 0]])
    loss_orthogonal = cosine(y_true, y_pred)
    assert np.isclose(loss_orthogonal, 1.0)
    
    print("✓ Cosine similarity loss basic test passed")


def test_triplet_loss_basic():
    """Test basic triplet loss functionality."""
    print("Testing triplet loss basic...")
    
    triplet = TripletLoss(margin=1.0)
    
    # Good triplet (positive closer than negative)
    anchor = np.array([[1, 2], [3, 4]])
    positive = np.array([[1.1, 2.1], [3.1, 4.1]])
    negative = np.array([[10, 10], [10, 10]])
    
    loss = triplet(anchor, positive, negative)
    assert loss < 0.01
    
    # Bad triplet (negative closer than positive)
    negative = np.array([[1.05, 2.05], [3.05, 4.05]])
    loss_bad = triplet(anchor, positive, negative)
    assert loss_bad > 0
    
    print("✓ Triplet loss basic test passed")


def test_mse_gradient():
    """Test MSE gradient computation."""
    print("Testing MSE gradient...")
    
    mse = MSE()
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    
    grad = mse.gradient(y_true, y_pred)
    assert grad.shape == y_true.shape
    
    print("✓ MSE gradient test passed")


def test_mae_gradient():
    """Test MAE gradient computation."""
    print("Testing MAE gradient...")
    
    mae = MAE()
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    
    grad = mae.gradient(y_true, y_pred)
    assert grad.shape == y_true.shape
    
    print("✓ MAE gradient test passed")


def test_huber_gradient():
    """Test Huber loss gradient computation."""
    print("Testing Huber gradient...")
    
    huber = HuberLoss(delta=1.0)
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 5.0])
    
    grad = huber.gradient(y_true, y_pred)
    assert grad.shape == y_true.shape
    
    print("✓ Huber gradient test passed")


def test_convenience_functions():
    """Test convenience functions."""
    print("Testing convenience functions...")
    
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    
    # MSE
    loss = mse_loss(y_true, y_pred)
    assert loss > 0
    
    # MAE
    loss = mae_loss(y_true, y_pred)
    assert loss > 0
    
    # Huber
    loss = huber_loss(y_true, y_pred, delta=1.0)
    assert loss > 0
    
    print("✓ Convenience functions test passed")


def test_classification_convenience_functions():
    """Test classification convenience functions."""
    print("Testing classification convenience functions...")
    
    # Cross entropy
    y_true = np.array([[1, 0, 0], [0, 1, 0]])
    y_pred = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]])
    loss = cross_entropy_loss(y_true, y_pred)
    assert loss > 0
    
    # Binary cross entropy
    y_true_bin = np.array([1, 0, 1, 0])
    y_pred_bin = np.array([0.9, 0.1, 0.8, 0.2])
    loss = binary_cross_entropy_loss(y_true_bin, y_pred_bin)
    assert loss > 0
    
    # Focal loss
    loss = focal_loss(y_true_bin, y_pred_bin, alpha=0.25, gamma=2.0)
    assert loss > 0
    
    print("✓ Classification convenience functions test passed")


def test_shape_mismatch():
    """Test error handling for shape mismatch."""
    print("Testing shape mismatch...")
    
    mse = MSE()
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0])
    
    try:
        loss = mse(y_true, y_pred)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Shape mismatch test passed")


def test_invalid_reduction():
    """Test error handling for invalid reduction."""
    print("Testing invalid reduction...")
    
    try:
        mse = MSE(reduction='invalid')
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Invalid reduction test passed")


def test_numerical_stability():
    """Test numerical stability with extreme values."""
    print("Testing numerical stability...")
    
    # Cross entropy with very small probabilities
    ce = CrossEntropy()
    y_true = np.array([[1, 0, 0]])
    y_pred = np.array([[0.999999, 0.0000005, 0.0000005]])
    
    loss = ce(y_true, y_pred)
    assert np.isfinite(loss)
    
    # Binary cross entropy with extreme values
    bce = BinaryCrossEntropy()
    y_true = np.array([1, 0])
    y_pred = np.array([0.999999, 0.000001])
    
    loss = bce(y_true, y_pred)
    assert np.isfinite(loss)
    
    print("✓ Numerical stability test passed")


def test_batch_processing():
    """Test loss functions with batched inputs."""
    print("Testing batch processing...")
    
    batch_size = 32
    
    # MSE with batches
    mse = MSE()
    y_true = np.random.randn(batch_size, 10)
    y_pred = np.random.randn(batch_size, 10)
    loss = mse(y_true, y_pred)
    assert np.isscalar(loss)
    
    # Cross entropy with batches
    ce = CrossEntropy()
    y_true = np.zeros((batch_size, 5))
    y_true[np.arange(batch_size), np.random.randint(0, 5, batch_size)] = 1
    y_pred = np.random.rand(batch_size, 5)
    y_pred = y_pred / y_pred.sum(axis=1, keepdims=True)
    loss = ce(y_true, y_pred)
    assert np.isscalar(loss)
    
    print("✓ Batch processing test passed")


def test_zero_loss():
    """Test that perfect predictions give zero loss."""
    print("Testing zero loss...")
    
    # MSE
    mse = MSE()
    y = np.array([1.0, 2.0, 3.0])
    assert np.isclose(mse(y, y), 0.0)
    
    # MAE
    mae = MAE()
    assert np.isclose(mae(y, y), 0.0)
    
    # Dice
    dice = DiceLoss()
    y_seg = np.array([[1, 1, 0, 0]])
    assert dice(y_seg, y_seg) < 0.01
    
    print("✓ Zero loss test passed")


def run_all_tests():
    """Run all loss function tests."""
    print("=" * 80)
    print("RUNNING LOSS FUNCTIONS TESTS")
    print("=" * 80)
    print()
    
    tests = [
        test_mse_basic,
        test_mse_reduction,
        test_mae_basic,
        test_huber_loss_basic,
        test_cross_entropy_basic,
        test_cross_entropy_from_logits,
        test_binary_cross_entropy_basic,
        test_focal_loss_basic,
        test_dice_loss_basic,
        test_hinge_loss_basic,
        test_kl_divergence_basic,
        test_cosine_similarity_loss_basic,
        test_triplet_loss_basic,
        test_mse_gradient,
        test_mae_gradient,
        test_huber_gradient,
        test_convenience_functions,
        test_classification_convenience_functions,
        test_shape_mismatch,
        test_invalid_reduction,
        test_numerical_stability,
        test_batch_processing,
        test_zero_loss,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
