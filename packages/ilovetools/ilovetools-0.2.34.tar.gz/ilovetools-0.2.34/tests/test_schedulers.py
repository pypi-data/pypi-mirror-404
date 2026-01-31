"""
Tests for Learning Rate Schedulers

This file contains comprehensive tests for all learning rate schedulers.

Author: Ali Mehdi
Date: January 17, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.schedulers import (
    StepLR,
    ExponentialLR,
    CosineAnnealingLR,
    CosineAnnealingWarmRestarts,
    OneCycleLR,
    CyclicLR,
    ReduceLROnPlateau,
    PolynomialLR,
    WarmupLR,
    MultiStepLR,
)


# ============================================================================
# TEST STEP LR
# ============================================================================

def test_step_lr_basic():
    """Test basic StepLR functionality."""
    scheduler = StepLR(initial_lr=0.1, step_size=10, gamma=0.1)
    
    # Epoch 0-9: lr = 0.1
    assert np.isclose(scheduler.step(0), 0.1)
    assert np.isclose(scheduler.step(5), 0.1)
    assert np.isclose(scheduler.step(9), 0.1)
    
    # Epoch 10-19: lr = 0.01
    assert np.isclose(scheduler.step(10), 0.01)
    assert np.isclose(scheduler.step(15), 0.01)
    
    # Epoch 20-29: lr = 0.001
    assert np.isclose(scheduler.step(20), 0.001)


def test_step_lr_get_lr():
    """Test StepLR get_lr method."""
    scheduler = StepLR(initial_lr=0.1, step_size=10, gamma=0.1)
    scheduler.step(15)
    assert np.isclose(scheduler.get_lr(), 0.01)


def test_step_lr_invalid_params():
    """Test StepLR with invalid parameters."""
    with pytest.raises(ValueError):
        StepLR(initial_lr=-0.1, step_size=10)
    
    with pytest.raises(ValueError):
        StepLR(initial_lr=0.1, step_size=-10)
    
    with pytest.raises(ValueError):
        StepLR(initial_lr=0.1, step_size=10, gamma=1.5)


# ============================================================================
# TEST EXPONENTIAL LR
# ============================================================================

def test_exponential_lr_basic():
    """Test basic ExponentialLR functionality."""
    scheduler = ExponentialLR(initial_lr=0.1, gamma=0.9)
    
    assert np.isclose(scheduler.step(0), 0.1)
    assert np.isclose(scheduler.step(1), 0.09)
    assert np.isclose(scheduler.step(10), 0.1 * (0.9 ** 10))


def test_exponential_lr_decay():
    """Test ExponentialLR decay pattern."""
    scheduler = ExponentialLR(initial_lr=1.0, gamma=0.5)
    
    lrs = [scheduler.step(i) for i in range(5)]
    # Should be: [1.0, 0.5, 0.25, 0.125, 0.0625]
    expected = [1.0 * (0.5 ** i) for i in range(5)]
    
    assert np.allclose(lrs, expected)


# ============================================================================
# TEST COSINE ANNEALING LR
# ============================================================================

def test_cosine_annealing_lr_basic():
    """Test basic CosineAnnealingLR functionality."""
    scheduler = CosineAnnealingLR(initial_lr=0.1, T_max=100, eta_min=0)
    
    # At epoch 0, lr should be initial_lr
    assert np.isclose(scheduler.step(0), 0.1)
    
    # At epoch T_max, lr should be eta_min
    assert np.isclose(scheduler.step(100), 0.0, atol=1e-6)
    
    # At epoch T_max/2, lr should be around middle
    lr_mid = scheduler.step(50)
    assert 0 < lr_mid < 0.1


def test_cosine_annealing_lr_with_min():
    """Test CosineAnnealingLR with non-zero minimum."""
    scheduler = CosineAnnealingLR(initial_lr=0.1, T_max=100, eta_min=0.01)
    
    # At epoch T_max, lr should be eta_min
    assert np.isclose(scheduler.step(100), 0.01, atol=1e-6)


# ============================================================================
# TEST COSINE ANNEALING WARM RESTARTS
# ============================================================================

def test_cosine_annealing_warm_restarts_basic():
    """Test basic CosineAnnealingWarmRestarts functionality."""
    scheduler = CosineAnnealingWarmRestarts(initial_lr=0.1, T_0=10, T_mult=1)
    
    lrs = [scheduler.step(i) for i in range(30)]
    
    # Should restart every 10 epochs
    assert np.isclose(lrs[0], 0.1)
    assert np.isclose(lrs[10], 0.1)
    assert np.isclose(lrs[20], 0.1)


def test_cosine_annealing_warm_restarts_mult():
    """Test CosineAnnealingWarmRestarts with T_mult > 1."""
    scheduler = CosineAnnealingWarmRestarts(initial_lr=0.1, T_0=10, T_mult=2)
    
    # First cycle: 10 epochs
    # Second cycle: 20 epochs
    # Third cycle: 40 epochs
    lrs = [scheduler.step(i) for i in range(50)]
    
    assert np.isclose(lrs[0], 0.1)  # Start of cycle 1
    assert np.isclose(lrs[10], 0.1)  # Start of cycle 2
    assert np.isclose(lrs[30], 0.1)  # Start of cycle 3


# ============================================================================
# TEST ONE CYCLE LR
# ============================================================================

def test_one_cycle_lr_basic():
    """Test basic OneCycleLR functionality."""
    scheduler = OneCycleLR(initial_lr=0.001, max_lr=0.1, total_steps=1000)
    
    # At step 0, lr should be initial_lr
    assert np.isclose(scheduler.step(0), 0.001)
    
    # At some point, lr should reach max_lr
    lrs = [scheduler.step(i) for i in range(1000)]
    assert np.isclose(max(lrs), 0.1, atol=1e-3)
    
    # At final step, lr should be close to final_lr
    assert lrs[-1] < 0.001


def test_one_cycle_lr_phases():
    """Test OneCycleLR phases."""
    scheduler = OneCycleLR(initial_lr=0.001, max_lr=0.1, total_steps=100, pct_start=0.3)
    
    # Phase 1: Increasing (0-30 steps)
    lr_0 = scheduler.step(0)
    lr_15 = scheduler.step(15)
    lr_30 = scheduler.step(30)
    
    assert lr_0 < lr_15 < lr_30
    
    # Phase 2: Decreasing (30-100 steps)
    lr_50 = scheduler.step(50)
    lr_75 = scheduler.step(75)
    lr_99 = scheduler.step(99)
    
    assert lr_30 > lr_50 > lr_75 > lr_99


# ============================================================================
# TEST CYCLIC LR
# ============================================================================

def test_cyclic_lr_triangular():
    """Test CyclicLR with triangular mode."""
    scheduler = CyclicLR(base_lr=0.001, max_lr=0.1, step_size=100, mode='triangular')
    
    lrs = [scheduler.step(i) for i in range(400)]
    
    # Should oscillate between base_lr and max_lr
    assert np.isclose(min(lrs), 0.001, atol=1e-3)
    assert np.isclose(max(lrs), 0.1, atol=1e-3)


def test_cyclic_lr_triangular2():
    """Test CyclicLR with triangular2 mode."""
    scheduler = CyclicLR(base_lr=0.001, max_lr=0.1, step_size=100, mode='triangular2')
    
    lrs = [scheduler.step(i) for i in range(400)]
    
    # Amplitude should decrease over cycles
    cycle1_max = max(lrs[0:200])
    cycle2_max = max(lrs[200:400])
    
    assert cycle1_max > cycle2_max


# ============================================================================
# TEST REDUCE LR ON PLATEAU
# ============================================================================

def test_reduce_lr_on_plateau_min_mode():
    """Test ReduceLROnPlateau in min mode."""
    scheduler = ReduceLROnPlateau(initial_lr=0.1, mode='min', patience=3, factor=0.1)
    
    # Improving metrics - no reduction
    scheduler.step(1.0)
    scheduler.step(0.9)
    scheduler.step(0.8)
    assert np.isclose(scheduler.get_lr(), 0.1)
    
    # Plateau - should reduce after patience epochs
    scheduler.step(0.8)
    scheduler.step(0.8)
    scheduler.step(0.8)
    assert np.isclose(scheduler.get_lr(), 0.01)


def test_reduce_lr_on_plateau_max_mode():
    """Test ReduceLROnPlateau in max mode."""
    scheduler = ReduceLROnPlateau(initial_lr=0.1, mode='max', patience=2, factor=0.5)
    
    # Improving metrics - no reduction
    scheduler.step(0.8)
    scheduler.step(0.9)
    assert np.isclose(scheduler.get_lr(), 0.1)
    
    # Plateau - should reduce
    scheduler.step(0.9)
    scheduler.step(0.9)
    assert np.isclose(scheduler.get_lr(), 0.05)


# ============================================================================
# TEST POLYNOMIAL LR
# ============================================================================

def test_polynomial_lr_linear():
    """Test PolynomialLR with power=1 (linear decay)."""
    scheduler = PolynomialLR(initial_lr=0.1, total_epochs=100, end_lr=0, power=1.0)
    
    assert np.isclose(scheduler.step(0), 0.1)
    assert np.isclose(scheduler.step(50), 0.05)
    assert np.isclose(scheduler.step(100), 0.0, atol=1e-6)


def test_polynomial_lr_quadratic():
    """Test PolynomialLR with power=2 (quadratic decay)."""
    scheduler = PolynomialLR(initial_lr=0.1, total_epochs=100, end_lr=0, power=2.0)
    
    lr_0 = scheduler.step(0)
    lr_50 = scheduler.step(50)
    lr_100 = scheduler.step(100)
    
    assert np.isclose(lr_0, 0.1)
    assert lr_50 > 0.025  # Slower decay than linear
    assert np.isclose(lr_100, 0.0, atol=1e-6)


# ============================================================================
# TEST WARMUP LR
# ============================================================================

def test_warmup_lr_basic():
    """Test basic WarmupLR functionality."""
    scheduler = WarmupLR(target_lr=0.1, warmup_steps=100)
    
    assert np.isclose(scheduler.step(0), 0.0)
    assert np.isclose(scheduler.step(50), 0.05)
    assert np.isclose(scheduler.step(100), 0.1)
    assert np.isclose(scheduler.step(150), 0.1)


def test_warmup_lr_linear_increase():
    """Test WarmupLR linear increase."""
    scheduler = WarmupLR(target_lr=1.0, warmup_steps=10)
    
    lrs = [scheduler.step(i) for i in range(15)]
    
    # Should increase linearly during warmup
    for i in range(10):
        expected = i / 10
        assert np.isclose(lrs[i], expected)
    
    # Should stay at target after warmup
    assert all(np.isclose(lr, 1.0) for lr in lrs[10:])


# ============================================================================
# TEST MULTI STEP LR
# ============================================================================

def test_multi_step_lr_basic():
    """Test basic MultiStepLR functionality."""
    scheduler = MultiStepLR(initial_lr=0.1, milestones=[30, 60, 90], gamma=0.1)
    
    # Before first milestone
    assert np.isclose(scheduler.step(0), 0.1)
    assert np.isclose(scheduler.step(29), 0.1)
    
    # After first milestone
    assert np.isclose(scheduler.step(30), 0.01)
    assert np.isclose(scheduler.step(59), 0.01)
    
    # After second milestone
    assert np.isclose(scheduler.step(60), 0.001)
    assert np.isclose(scheduler.step(89), 0.001)
    
    # After third milestone
    assert np.isclose(scheduler.step(90), 0.0001)


def test_multi_step_lr_unordered_milestones():
    """Test MultiStepLR with unordered milestones."""
    scheduler = MultiStepLR(initial_lr=0.1, milestones=[60, 30, 90], gamma=0.1)
    
    # Should sort milestones internally
    assert np.isclose(scheduler.step(30), 0.01)
    assert np.isclose(scheduler.step(60), 0.001)
    assert np.isclose(scheduler.step(90), 0.0001)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_scheduler_sequence():
    """Test using multiple schedulers in sequence."""
    # Warmup for 100 steps
    warmup = WarmupLR(target_lr=0.1, warmup_steps=100)
    
    # Then cosine annealing
    cosine = CosineAnnealingLR(initial_lr=0.1, T_max=900, eta_min=0)
    
    lrs = []
    for step in range(1000):
        if step < 100:
            lr = warmup.step(step)
        else:
            lr = cosine.step(step - 100)
        lrs.append(lr)
    
    # Should start at 0, increase to 0.1, then decrease
    assert np.isclose(lrs[0], 0.0)
    assert np.isclose(lrs[100], 0.1, atol=1e-3)
    assert lrs[999] < 0.01


def test_all_schedulers_return_positive_lr():
    """Test that all schedulers return positive learning rates."""
    schedulers = [
        StepLR(initial_lr=0.1, step_size=10),
        ExponentialLR(initial_lr=0.1, gamma=0.9),
        CosineAnnealingLR(initial_lr=0.1, T_max=100),
        CosineAnnealingWarmRestarts(initial_lr=0.1, T_0=10),
        OneCycleLR(initial_lr=0.001, max_lr=0.1, total_steps=100),
        CyclicLR(base_lr=0.001, max_lr=0.1, step_size=50),
        PolynomialLR(initial_lr=0.1, total_epochs=100),
        WarmupLR(target_lr=0.1, warmup_steps=100),
        MultiStepLR(initial_lr=0.1, milestones=[30, 60]),
    ]
    
    for scheduler in schedulers:
        for i in range(100):
            lr = scheduler.step(i)
            assert lr >= 0, f"{scheduler.__class__.__name__} returned negative LR"


def test_scheduler_reproducibility():
    """Test that schedulers are reproducible."""
    scheduler1 = CosineAnnealingLR(initial_lr=0.1, T_max=100)
    scheduler2 = CosineAnnealingLR(initial_lr=0.1, T_max=100)
    
    lrs1 = [scheduler1.step(i) for i in range(100)]
    lrs2 = [scheduler2.step(i) for i in range(100)]
    
    assert np.allclose(lrs1, lrs2)


print("=" * 80)
print("ALL SCHEDULER TESTS PASSED! ✓")
print("=" * 80)
