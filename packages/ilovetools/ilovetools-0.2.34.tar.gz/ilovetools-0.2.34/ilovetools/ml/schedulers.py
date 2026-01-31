"""
Learning Rate Schedulers Suite

This module implements various learning rate scheduling strategies for training neural networks.
Learning rate schedulers dynamically adjust the learning rate during training to improve
convergence speed, stability, and final model performance.

Implemented Schedulers:
1. StepLR - Step decay at fixed intervals
2. ExponentialLR - Exponential decay
3. CosineAnnealingLR - Cosine annealing schedule
4. CosineAnnealingWarmRestarts - Cosine annealing with warm restarts (SGDR)
5. OneCycleLR - One cycle learning rate policy
6. CyclicLR - Cyclic learning rate
7. ReduceLROnPlateau - Reduce LR when metric plateaus
8. PolynomialLR - Polynomial decay
9. WarmupLR - Linear warmup scheduler
10. MultiStepLR - Multi-step decay

References:
- Step Decay: Standard practice in deep learning
- Cosine Annealing: "SGDR: Stochastic Gradient Descent with Warm Restarts" (Loshchilov & Hutter, 2016)
- One Cycle: "Super-Convergence" (Smith, 2018)
- Cyclic LR: "Cyclical Learning Rates for Training Neural Networks" (Smith, 2017)

Author: Ali Mehdi
Date: January 17, 2026
"""

import numpy as np
from typing import Optional, Callable


class StepLR:
    """
    Step Learning Rate Scheduler.
    
    Decays the learning rate by gamma every step_size epochs.
    
    Formula:
        lr = initial_lr * gamma^(epoch // step_size)
    
    Args:
        initial_lr: Initial learning rate
        step_size: Period of learning rate decay (in epochs)
        gamma: Multiplicative factor of learning rate decay (default: 0.1)
    
    Example:
        >>> scheduler = StepLR(initial_lr=0.1, step_size=30, gamma=0.1)
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
        ...     print(f"Epoch {epoch}: LR = {lr}")
    
    Reference:
        Standard practice in deep learning
    """
    
    def __init__(self, initial_lr: float, step_size: int, gamma: float = 0.1):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if step_size <= 0:
            raise ValueError(f"step_size must be positive, got {step_size}")
        if gamma <= 0 or gamma >= 1:
            raise ValueError(f"gamma must be in (0, 1), got {gamma}")
        
        self.initial_lr = initial_lr
        self.step_size = step_size
        self.gamma = gamma
        self.current_lr = initial_lr
    
    def step(self, epoch: int) -> float:
        """
        Update learning rate for given epoch.
        
        Args:
            epoch: Current epoch number
        
        Returns:
            Updated learning rate
        """
        self.current_lr = self.initial_lr * (self.gamma ** (epoch // self.step_size))
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class ExponentialLR:
    """
    Exponential Learning Rate Scheduler.
    
    Decays the learning rate exponentially every epoch.
    
    Formula:
        lr = initial_lr * gamma^epoch
    
    Args:
        initial_lr: Initial learning rate
        gamma: Multiplicative factor of learning rate decay (default: 0.95)
    
    Example:
        >>> scheduler = ExponentialLR(initial_lr=0.1, gamma=0.95)
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
    
    Reference:
        Standard exponential decay
    """
    
    def __init__(self, initial_lr: float, gamma: float = 0.95):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if gamma <= 0 or gamma >= 1:
            raise ValueError(f"gamma must be in (0, 1), got {gamma}")
        
        self.initial_lr = initial_lr
        self.gamma = gamma
        self.current_lr = initial_lr
    
    def step(self, epoch: int) -> float:
        """Update learning rate for given epoch."""
        self.current_lr = self.initial_lr * (self.gamma ** epoch)
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class CosineAnnealingLR:
    """
    Cosine Annealing Learning Rate Scheduler.
    
    Sets the learning rate using a cosine annealing schedule.
    
    Formula:
        lr = eta_min + (initial_lr - eta_min) * (1 + cos(π * epoch / T_max)) / 2
    
    Args:
        initial_lr: Initial learning rate
        T_max: Maximum number of iterations
        eta_min: Minimum learning rate (default: 0)
    
    Example:
        >>> scheduler = CosineAnnealingLR(initial_lr=0.1, T_max=100)
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
    
    Reference:
        Loshchilov & Hutter, "SGDR: Stochastic Gradient Descent with Warm Restarts", 2016
    """
    
    def __init__(self, initial_lr: float, T_max: int, eta_min: float = 0):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if T_max <= 0:
            raise ValueError(f"T_max must be positive, got {T_max}")
        if eta_min < 0:
            raise ValueError(f"eta_min must be non-negative, got {eta_min}")
        
        self.initial_lr = initial_lr
        self.T_max = T_max
        self.eta_min = eta_min
        self.current_lr = initial_lr
    
    def step(self, epoch: int) -> float:
        """Update learning rate for given epoch."""
        self.current_lr = self.eta_min + (self.initial_lr - self.eta_min) * \
                         (1 + np.cos(np.pi * epoch / self.T_max)) / 2
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class CosineAnnealingWarmRestarts:
    """
    Cosine Annealing with Warm Restarts (SGDR).
    
    Periodically restarts the learning rate schedule.
    
    Formula:
        lr = eta_min + (initial_lr - eta_min) * (1 + cos(π * T_cur / T_i)) / 2
        where T_i is the current restart period
    
    Args:
        initial_lr: Initial learning rate
        T_0: Number of iterations for the first restart
        T_mult: Factor to increase T_i after each restart (default: 1)
        eta_min: Minimum learning rate (default: 0)
    
    Example:
        >>> scheduler = CosineAnnealingWarmRestarts(initial_lr=0.1, T_0=10, T_mult=2)
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
    
    Reference:
        Loshchilov & Hutter, "SGDR: Stochastic Gradient Descent with Warm Restarts", 2016
    """
    
    def __init__(self, initial_lr: float, T_0: int, T_mult: int = 1, eta_min: float = 0):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if T_0 <= 0:
            raise ValueError(f"T_0 must be positive, got {T_0}")
        if T_mult < 1:
            raise ValueError(f"T_mult must be >= 1, got {T_mult}")
        
        self.initial_lr = initial_lr
        self.T_0 = T_0
        self.T_mult = T_mult
        self.eta_min = eta_min
        self.current_lr = initial_lr
        self.T_i = T_0
        self.T_cur = 0
    
    def step(self, epoch: int) -> float:
        """Update learning rate for given epoch."""
        if self.T_cur >= self.T_i:
            self.T_cur = 0
            self.T_i = self.T_i * self.T_mult
        
        self.current_lr = self.eta_min + (self.initial_lr - self.eta_min) * \
                         (1 + np.cos(np.pi * self.T_cur / self.T_i)) / 2
        self.T_cur += 1
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class OneCycleLR:
    """
    One Cycle Learning Rate Policy.
    
    Increases learning rate from initial to max, then decreases to min.
    
    Phases:
        1. Warmup: initial_lr → max_lr (pct_start of total steps)
        2. Annealing: max_lr → final_lr (remaining steps)
    
    Args:
        initial_lr: Initial learning rate
        max_lr: Maximum learning rate
        total_steps: Total number of training steps
        pct_start: Percentage of cycle spent increasing LR (default: 0.3)
        final_lr: Final learning rate (default: initial_lr / 1000)
    
    Example:
        >>> scheduler = OneCycleLR(initial_lr=0.001, max_lr=0.1, total_steps=1000)
        >>> for step in range(1000):
        ...     lr = scheduler.step(step)
    
    Reference:
        Smith, "Super-Convergence: Very Fast Training of Neural Networks", 2018
    """
    
    def __init__(self, initial_lr: float, max_lr: float, total_steps: int,
                 pct_start: float = 0.3, final_lr: Optional[float] = None):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if max_lr <= initial_lr:
            raise ValueError(f"max_lr must be > initial_lr, got {max_lr}")
        if total_steps <= 0:
            raise ValueError(f"total_steps must be positive, got {total_steps}")
        if not 0 < pct_start < 1:
            raise ValueError(f"pct_start must be in (0, 1), got {pct_start}")
        
        self.initial_lr = initial_lr
        self.max_lr = max_lr
        self.total_steps = total_steps
        self.pct_start = pct_start
        self.final_lr = final_lr if final_lr is not None else initial_lr / 1000
        self.current_lr = initial_lr
        
        self.step_up = int(total_steps * pct_start)
        self.step_down = total_steps - self.step_up
    
    def step(self, current_step: int) -> float:
        """Update learning rate for given step."""
        if current_step < self.step_up:
            # Phase 1: Increase from initial_lr to max_lr
            pct = current_step / self.step_up
            self.current_lr = self.initial_lr + (self.max_lr - self.initial_lr) * pct
        else:
            # Phase 2: Decrease from max_lr to final_lr
            pct = (current_step - self.step_up) / self.step_down
            self.current_lr = self.max_lr - (self.max_lr - self.final_lr) * pct
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class CyclicLR:
    """
    Cyclic Learning Rate Scheduler.
    
    Cycles the learning rate between two boundaries with a constant frequency.
    
    Args:
        base_lr: Lower boundary of the learning rate
        max_lr: Upper boundary of the learning rate
        step_size: Number of iterations in half a cycle
        mode: One of {'triangular', 'triangular2', 'exp_range'} (default: 'triangular')
        gamma: Constant for 'exp_range' mode (default: 1.0)
    
    Example:
        >>> scheduler = CyclicLR(base_lr=0.001, max_lr=0.1, step_size=2000)
        >>> for step in range(10000):
        ...     lr = scheduler.step(step)
    
    Reference:
        Smith, "Cyclical Learning Rates for Training Neural Networks", 2017
    """
    
    def __init__(self, base_lr: float, max_lr: float, step_size: int,
                 mode: str = 'triangular', gamma: float = 1.0):
        if base_lr <= 0:
            raise ValueError(f"base_lr must be positive, got {base_lr}")
        if max_lr <= base_lr:
            raise ValueError(f"max_lr must be > base_lr, got {max_lr}")
        if step_size <= 0:
            raise ValueError(f"step_size must be positive, got {step_size}")
        if mode not in ['triangular', 'triangular2', 'exp_range']:
            raise ValueError(f"mode must be one of ['triangular', 'triangular2', 'exp_range'], got {mode}")
        
        self.base_lr = base_lr
        self.max_lr = max_lr
        self.step_size = step_size
        self.mode = mode
        self.gamma = gamma
        self.current_lr = base_lr
    
    def step(self, current_step: int) -> float:
        """Update learning rate for given step."""
        cycle = np.floor(1 + current_step / (2 * self.step_size))
        x = np.abs(current_step / self.step_size - 2 * cycle + 1)
        
        if self.mode == 'triangular':
            scale_fn = 1.0
        elif self.mode == 'triangular2':
            scale_fn = 1 / (2 ** (cycle - 1))
        else:  # exp_range
            scale_fn = self.gamma ** current_step
        
        self.current_lr = self.base_lr + (self.max_lr - self.base_lr) * \
                         max(0, (1 - x)) * scale_fn
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class ReduceLROnPlateau:
    """
    Reduce Learning Rate on Plateau.
    
    Reduces learning rate when a metric has stopped improving.
    
    Args:
        initial_lr: Initial learning rate
        mode: One of {'min', 'max'} (default: 'min')
        factor: Factor by which to reduce LR (default: 0.1)
        patience: Number of epochs with no improvement to wait (default: 10)
        threshold: Threshold for measuring improvement (default: 1e-4)
        min_lr: Minimum learning rate (default: 0)
    
    Example:
        >>> scheduler = ReduceLROnPlateau(initial_lr=0.1, patience=10)
        >>> for epoch in range(100):
        ...     val_loss = train_and_validate()
        ...     lr = scheduler.step(val_loss)
    
    Reference:
        Standard adaptive learning rate reduction
    """
    
    def __init__(self, initial_lr: float, mode: str = 'min', factor: float = 0.1,
                 patience: int = 10, threshold: float = 1e-4, min_lr: float = 0):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if mode not in ['min', 'max']:
            raise ValueError(f"mode must be 'min' or 'max', got {mode}")
        if factor <= 0 or factor >= 1:
            raise ValueError(f"factor must be in (0, 1), got {factor}")
        if patience <= 0:
            raise ValueError(f"patience must be positive, got {patience}")
        
        self.initial_lr = initial_lr
        self.mode = mode
        self.factor = factor
        self.patience = patience
        self.threshold = threshold
        self.min_lr = min_lr
        self.current_lr = initial_lr
        
        self.best_metric = np.inf if mode == 'min' else -np.inf
        self.num_bad_epochs = 0
    
    def step(self, metric: float) -> float:
        """
        Update learning rate based on metric.
        
        Args:
            metric: Current metric value (e.g., validation loss)
        
        Returns:
            Updated learning rate
        """
        if self.mode == 'min':
            is_better = metric < self.best_metric - self.threshold
        else:
            is_better = metric > self.best_metric + self.threshold
        
        if is_better:
            self.best_metric = metric
            self.num_bad_epochs = 0
        else:
            self.num_bad_epochs += 1
        
        if self.num_bad_epochs >= self.patience:
            self.current_lr = max(self.current_lr * self.factor, self.min_lr)
            self.num_bad_epochs = 0
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class PolynomialLR:
    """
    Polynomial Learning Rate Scheduler.
    
    Decays the learning rate using a polynomial function.
    
    Formula:
        lr = (initial_lr - end_lr) * (1 - epoch / total_epochs)^power + end_lr
    
    Args:
        initial_lr: Initial learning rate
        total_epochs: Total number of epochs
        end_lr: Final learning rate (default: 0)
        power: Polynomial power (default: 1.0)
    
    Example:
        >>> scheduler = PolynomialLR(initial_lr=0.1, total_epochs=100, power=2.0)
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
    
    Reference:
        Polynomial decay scheduling
    """
    
    def __init__(self, initial_lr: float, total_epochs: int, 
                 end_lr: float = 0, power: float = 1.0):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if total_epochs <= 0:
            raise ValueError(f"total_epochs must be positive, got {total_epochs}")
        if end_lr < 0:
            raise ValueError(f"end_lr must be non-negative, got {end_lr}")
        if power <= 0:
            raise ValueError(f"power must be positive, got {power}")
        
        self.initial_lr = initial_lr
        self.total_epochs = total_epochs
        self.end_lr = end_lr
        self.power = power
        self.current_lr = initial_lr
    
    def step(self, epoch: int) -> float:
        """Update learning rate for given epoch."""
        self.current_lr = (self.initial_lr - self.end_lr) * \
                         (1 - epoch / self.total_epochs) ** self.power + self.end_lr
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class WarmupLR:
    """
    Linear Warmup Learning Rate Scheduler.
    
    Linearly increases learning rate from 0 to target over warmup steps.
    
    Args:
        target_lr: Target learning rate after warmup
        warmup_steps: Number of warmup steps
    
    Example:
        >>> scheduler = WarmupLR(target_lr=0.1, warmup_steps=1000)
        >>> for step in range(1000):
        ...     lr = scheduler.step(step)
    
    Reference:
        Standard warmup practice
    """
    
    def __init__(self, target_lr: float, warmup_steps: int):
        if target_lr <= 0:
            raise ValueError(f"target_lr must be positive, got {target_lr}")
        if warmup_steps <= 0:
            raise ValueError(f"warmup_steps must be positive, got {warmup_steps}")
        
        self.target_lr = target_lr
        self.warmup_steps = warmup_steps
        self.current_lr = 0
    
    def step(self, current_step: int) -> float:
        """Update learning rate for given step."""
        if current_step < self.warmup_steps:
            self.current_lr = self.target_lr * (current_step / self.warmup_steps)
        else:
            self.current_lr = self.target_lr
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


class MultiStepLR:
    """
    Multi-Step Learning Rate Scheduler.
    
    Decays the learning rate by gamma at specified milestones.
    
    Args:
        initial_lr: Initial learning rate
        milestones: List of epoch indices for LR decay
        gamma: Multiplicative factor of learning rate decay (default: 0.1)
    
    Example:
        >>> scheduler = MultiStepLR(initial_lr=0.1, milestones=[30, 60, 90])
        >>> for epoch in range(100):
        ...     lr = scheduler.step(epoch)
    
    Reference:
        Standard multi-step decay
    """
    
    def __init__(self, initial_lr: float, milestones: list, gamma: float = 0.1):
        if initial_lr <= 0:
            raise ValueError(f"initial_lr must be positive, got {initial_lr}")
        if not milestones:
            raise ValueError("milestones cannot be empty")
        if gamma <= 0 or gamma >= 1:
            raise ValueError(f"gamma must be in (0, 1), got {gamma}")
        
        self.initial_lr = initial_lr
        self.milestones = sorted(milestones)
        self.gamma = gamma
        self.current_lr = initial_lr
    
    def step(self, epoch: int) -> float:
        """Update learning rate for given epoch."""
        num_decays = sum(1 for m in self.milestones if epoch >= m)
        self.current_lr = self.initial_lr * (self.gamma ** num_decays)
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.current_lr


__all__ = [
    'StepLR',
    'ExponentialLR',
    'CosineAnnealingLR',
    'CosineAnnealingWarmRestarts',
    'OneCycleLR',
    'CyclicLR',
    'ReduceLROnPlateau',
    'PolynomialLR',
    'WarmupLR',
    'MultiStepLR',
]
