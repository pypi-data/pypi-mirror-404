"""
Comprehensive tests for learning rate schedulers

Tests all scheduler implementations to ensure correctness
and proper functionality.
"""

import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.lr_schedulers import (
    # Scheduler Classes
    StepLRScheduler,
    ExponentialLRScheduler,
    CosineAnnealingLR,
    CosineAnnealingWarmRestarts,
    OneCycleLR,
    ReduceLROnPlateau,
    PolynomialLRScheduler,
    LinearWarmupScheduler,
    CyclicalLR,
    LRFinder,
    WarmupCosineScheduler,
    # Utility Functions
    get_scheduler,
    # Aliases
    step_lr,
    exp_lr,
    cosine_lr,
    sgdr,
    onecycle,
    plateau_lr,
    poly_lr,
    warmup_lr,
    cyclical_lr,
    lr_finder,
    warmup_cosine,
)


def test_step_lr_scheduler():
    """Test Step LR Scheduler"""
    print("Testing Step LR Scheduler...")
    
    initial_lr = 0.1
    step_size = 10
    gamma = 0.1
    
    scheduler = StepLRScheduler(initial_lr, step_size, gamma)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Test first step
    lr = scheduler.step(0)
    assert lr == initial_lr, "LR at epoch 0 should be initial_lr"
    
    # Test before step
    lr = scheduler.step(9)
    assert lr == initial_lr, "LR should not decay before step_size"
    
    # Test at step
    lr = scheduler.step(10)
    expected_lr = initial_lr * gamma
    assert np.isclose(lr, expected_lr), f"LR at step should be {expected_lr}"
    
    # Test after multiple steps
    lr = scheduler.step(20)
    expected_lr = initial_lr * (gamma ** 2)
    assert np.isclose(lr, expected_lr), f"LR at 2*step should be {expected_lr}"
    
    print("✓ Step LR Scheduler tests passed")


def test_exponential_lr_scheduler():
    """Test Exponential LR Scheduler"""
    print("Testing Exponential LR Scheduler...")
    
    initial_lr = 0.1
    gamma = 0.95
    
    scheduler = ExponentialLRScheduler(initial_lr, gamma)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Test exponential decay
    for epoch in range(10):
        lr = scheduler.step()
        expected_lr = initial_lr * (gamma ** (epoch + 1))
        assert np.isclose(lr, expected_lr), f"LR at epoch {epoch+1} incorrect"
    
    print("✓ Exponential LR Scheduler tests passed")


def test_cosine_annealing_lr():
    """Test Cosine Annealing LR"""
    print("Testing Cosine Annealing LR...")
    
    initial_lr = 0.1
    T_max = 100
    eta_min = 0.001
    
    scheduler = CosineAnnealingLR(initial_lr, T_max, eta_min)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Test at halfway point
    lr = scheduler.step(T_max // 2)
    assert lr < initial_lr and lr > eta_min, "LR should be between min and max"
    
    # Test at end
    lr = scheduler.step(T_max)
    assert np.isclose(lr, eta_min, atol=1e-6), "LR should be close to eta_min at T_max"
    
    # Test monotonic decrease in first half
    scheduler2 = CosineAnnealingLR(initial_lr, T_max, eta_min)
    prev_lr = initial_lr
    for epoch in range(T_max // 2):
        lr = scheduler2.step()
        assert lr <= prev_lr, "LR should decrease in first half"
        prev_lr = lr
    
    print("✓ Cosine Annealing LR tests passed")


def test_cosine_annealing_warm_restarts():
    """Test Cosine Annealing with Warm Restarts"""
    print("Testing Cosine Annealing with Warm Restarts...")
    
    initial_lr = 0.1
    T_0 = 10
    T_mult = 2
    eta_min = 0.001
    
    scheduler = CosineAnnealingWarmRestarts(initial_lr, T_0, T_mult, eta_min)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Test first cycle
    lr_start = scheduler.step(0)
    lr_mid = scheduler.step(T_0 // 2)
    lr_end = scheduler.step(T_0 - 1)
    
    assert lr_start == initial_lr, "Should start at initial_lr"
    assert lr_mid < initial_lr, "Should decrease during cycle"
    assert lr_end < lr_mid, "Should continue decreasing"
    
    # Test restart
    lr_restart = scheduler.step(T_0)
    assert lr_restart > lr_end, "Should restart to higher LR"
    
    print("✓ Cosine Annealing with Warm Restarts tests passed")


def test_onecycle_lr():
    """Test One Cycle LR"""
    print("Testing One Cycle LR...")
    
    max_lr = 0.1
    total_steps = 100
    
    scheduler = OneCycleLR(max_lr, total_steps)
    
    lrs = []
    for _ in range(total_steps):
        lr = scheduler.step()
        lrs.append(lr)
    
    # Test that LR increases then decreases
    max_idx = np.argmax(lrs)
    assert max_idx > 0 and max_idx < total_steps - 1, "Peak should be in middle"
    
    # Test that max LR is reached
    assert np.isclose(max(lrs), max_lr, rtol=0.1), "Should reach max_lr"
    
    # Test that LR decreases after peak
    assert lrs[-1] < lrs[max_idx], "LR should decrease after peak"
    
    print("✓ One Cycle LR tests passed")


def test_reduce_lr_on_plateau():
    """Test Reduce LR on Plateau"""
    print("Testing Reduce LR on Plateau...")
    
    initial_lr = 0.1
    factor = 0.1
    patience = 3
    
    scheduler = ReduceLROnPlateau(initial_lr, mode='min', factor=factor, patience=patience)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Simulate improving metrics
    for i in range(patience):
        lr = scheduler.step(1.0 - i * 0.1)
        assert lr == initial_lr, "LR should not change when improving"
    
    # Simulate plateau
    for i in range(patience + 1):
        lr = scheduler.step(0.5)
    
    # LR should have reduced
    assert lr < initial_lr, "LR should reduce after plateau"
    assert np.isclose(lr, initial_lr * factor), "LR should be reduced by factor"
    
    print("✓ Reduce LR on Plateau tests passed")


def test_polynomial_lr_scheduler():
    """Test Polynomial LR Scheduler"""
    print("Testing Polynomial LR Scheduler...")
    
    initial_lr = 0.1
    total_steps = 100
    power = 2.0
    end_lr = 0.001
    
    scheduler = PolynomialLRScheduler(initial_lr, total_steps, power, end_lr)
    
    # Test initial LR
    assert scheduler.get_lr() == initial_lr, "Initial LR incorrect"
    
    # Test decay
    lrs = []
    for _ in range(total_steps):
        lr = scheduler.step()
        lrs.append(lr)
    
    # Test monotonic decrease
    for i in range(len(lrs) - 1):
        assert lrs[i] >= lrs[i+1], "LR should decrease monotonically"
    
    # Test final LR
    assert np.isclose(lrs[-1], end_lr, atol=1e-6), "Final LR should be end_lr"
    
    print("✓ Polynomial LR Scheduler tests passed")


def test_linear_warmup_scheduler():
    """Test Linear Warmup Scheduler"""
    print("Testing Linear Warmup Scheduler...")
    
    target_lr = 0.1
    warmup_steps = 10
    
    scheduler = LinearWarmupScheduler(target_lr, warmup_steps)
    
    # Test initial LR
    assert scheduler.get_lr() == 0, "Initial LR should be 0"
    
    # Test warmup
    lrs = []
    for _ in range(warmup_steps):
        lr = scheduler.step()
        lrs.append(lr)
    
    # Test monotonic increase
    for i in range(len(lrs) - 1):
        assert lrs[i] <= lrs[i+1], "LR should increase during warmup"
    
    # Test target reached
    assert np.isclose(lrs[-1], target_lr), "Should reach target_lr after warmup"
    
    # Test stays at target
    lr = scheduler.step()
    assert lr == target_lr, "Should stay at target_lr after warmup"
    
    print("✓ Linear Warmup Scheduler tests passed")


def test_cyclical_lr():
    """Test Cyclical LR"""
    print("Testing Cyclical LR...")
    
    base_lr = 0.001
    max_lr = 0.1
    step_size = 10
    
    scheduler = CyclicalLR(base_lr, max_lr, step_size, mode='triangular')
    
    # Test one complete cycle
    lrs = []
    for _ in range(2 * step_size):
        lr = scheduler.step()
        lrs.append(lr)
    
    # Test that LR cycles
    assert min(lrs) >= base_lr, "Min LR should be >= base_lr"
    assert max(lrs) <= max_lr, "Max LR should be <= max_lr"
    
    # Test triangular pattern
    mid_point = step_size
    assert lrs[mid_point] > lrs[0], "LR should increase in first half"
    assert lrs[-1] < lrs[mid_point], "LR should decrease in second half"
    
    print("✓ Cyclical LR tests passed")


def test_lr_finder():
    """Test LR Finder"""
    print("Testing LR Finder...")
    
    start_lr = 1e-7
    end_lr = 10
    num_steps = 50
    
    finder = LRFinder(start_lr, end_lr, num_steps)
    
    # Simulate training with decreasing then increasing loss
    for i in range(num_steps):
        # Simulate loss curve
        if i < num_steps // 2:
            loss = 2.0 - i * 0.05  # Decreasing
        else:
            loss = 1.0 + (i - num_steps // 2) * 0.1  # Increasing
        
        lr = finder.step(loss)
    
    # Test that LR increased
    assert finder.get_lr() > start_lr, "LR should have increased"
    
    # Test history
    lr_history, loss_history = finder.plot_results()
    assert len(lr_history) == num_steps, "Should have recorded all LRs"
    assert len(loss_history) == num_steps, "Should have recorded all losses"
    
    # Test suggestion
    suggested_lr = finder.suggest_lr()
    assert suggested_lr > start_lr and suggested_lr < end_lr, "Suggested LR should be in range"
    
    print("✓ LR Finder tests passed")


def test_warmup_cosine_scheduler():
    """Test Warmup + Cosine Scheduler"""
    print("Testing Warmup + Cosine Scheduler...")
    
    max_lr = 0.1
    warmup_steps = 10
    total_steps = 100
    
    scheduler = WarmupCosineScheduler(max_lr, warmup_steps, total_steps)
    
    # Test warmup phase
    lrs_warmup = []
    for _ in range(warmup_steps):
        lr = scheduler.step()
        lrs_warmup.append(lr)
    
    # Test warmup increases
    for i in range(len(lrs_warmup) - 1):
        assert lrs_warmup[i] <= lrs_warmup[i+1], "LR should increase during warmup"
    
    # Test reaches max_lr
    assert np.isclose(lrs_warmup[-1], max_lr, rtol=0.1), "Should reach max_lr"
    
    # Test cosine decay
    lrs_decay = []
    for _ in range(total_steps - warmup_steps):
        lr = scheduler.step()
        lrs_decay.append(lr)
    
    # Test decay decreases
    assert lrs_decay[-1] < lrs_decay[0], "LR should decrease after warmup"
    
    print("✓ Warmup + Cosine Scheduler tests passed")


def test_get_scheduler():
    """Test scheduler factory function"""
    print("Testing get_scheduler factory...")
    
    initial_lr = 0.1
    
    # Test creating different schedulers
    schedulers_to_test = [
        ('step', {'step_size': 10}),
        ('exponential', {'gamma': 0.95}),
        ('cosine', {'T_max': 100}),
        ('onecycle', {'total_steps': 100}),
        ('plateau', {}),
    ]
    
    for name, kwargs in schedulers_to_test:
        scheduler = get_scheduler(name, initial_lr, **kwargs)
        assert scheduler is not None, f"Failed to create {name} scheduler"
        assert hasattr(scheduler, 'step'), f"{name} scheduler missing step method"
        assert hasattr(scheduler, 'get_lr'), f"{name} scheduler missing get_lr method"
    
    # Test invalid scheduler
    try:
        get_scheduler('invalid', initial_lr)
        assert False, "Should raise error for invalid scheduler"
    except ValueError:
        pass
    
    print("✓ get_scheduler factory tests passed")


def test_aliases():
    """Test that aliases work correctly"""
    print("Testing aliases...")
    
    # Test scheduler aliases
    assert step_lr == StepLRScheduler
    assert exp_lr == ExponentialLRScheduler
    assert cosine_lr == CosineAnnealingLR
    assert sgdr == CosineAnnealingWarmRestarts
    assert onecycle == OneCycleLR
    assert plateau_lr == ReduceLROnPlateau
    assert poly_lr == PolynomialLRScheduler
    assert warmup_lr == LinearWarmupScheduler
    assert cyclical_lr == CyclicalLR
    assert lr_finder == LRFinder
    assert warmup_cosine == WarmupCosineScheduler
    
    print("✓ Aliases tests passed")


def test_integration_training_loop():
    """Test integration with simulated training loop"""
    print("Testing integration with training loop...")
    
    # Simulate training with OneCycle
    max_lr = 0.1
    total_steps = 100
    scheduler = OneCycleLR(max_lr, total_steps)
    
    losses = []
    lrs = []
    
    # Simulate training
    for step in range(total_steps):
        lr = scheduler.step()
        lrs.append(lr)
        
        # Simulate loss (should decrease with proper LR)
        loss = 2.0 * np.exp(-step / 50) + np.random.normal(0, 0.1)
        losses.append(loss)
    
    # Test that training progressed
    assert len(lrs) == total_steps, "Should have LR for each step"
    assert len(losses) == total_steps, "Should have loss for each step"
    
    # Test LR schedule was applied
    assert max(lrs) > min(lrs), "LR should have varied"
    
    print("✓ Integration with training loop tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("LEARNING RATE SCHEDULERS - COMPREHENSIVE TESTS")
    print("=" * 70)
    print()
    
    tests = [
        test_step_lr_scheduler,
        test_exponential_lr_scheduler,
        test_cosine_annealing_lr,
        test_cosine_annealing_warm_restarts,
        test_onecycle_lr,
        test_reduce_lr_on_plateau,
        test_polynomial_lr_scheduler,
        test_linear_warmup_scheduler,
        test_cyclical_lr,
        test_lr_finder,
        test_warmup_cosine_scheduler,
        test_get_scheduler,
        test_aliases,
        test_integration_training_loop,
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
        print("All learning rate schedulers are working correctly!")
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
