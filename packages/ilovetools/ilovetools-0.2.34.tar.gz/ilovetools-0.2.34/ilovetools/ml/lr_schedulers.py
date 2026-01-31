"""
Learning Rate Schedulers and Advanced Optimization Techniques Module

This module provides comprehensive implementations of learning rate scheduling
strategies and advanced optimization techniques for training deep learning models.

Features:
- Step Decay Scheduler
- Exponential Decay Scheduler
- Cosine Annealing Scheduler
- Cosine Annealing with Warm Restarts (SGDR)
- One Cycle Policy (Super-Convergence)
- Reduce on Plateau Scheduler
- Polynomial Decay Scheduler
- Linear Warmup Scheduler
- Cyclical Learning Rate
- Learning Rate Finder

Author: Ali Mehdi
License: MIT
"""

import numpy as np
from typing import Optional, Callable, List, Tuple


# ============================================================================
# LEARNING RATE SCHEDULERS
# ============================================================================

class StepLRScheduler:
    """
    Step Learning Rate Scheduler
    
    Decays the learning rate by gamma every step_size epochs.
    Commonly used in ResNet, VGG, and other classic architectures.
    
    Args:
        initial_lr: Initial learning rate
        step_size: Period of learning rate decay (in epochs)
        gamma: Multiplicative factor of learning rate decay
    """
    
    def __init__(self, initial_lr: float, step_size: int, gamma: float = 0.1):
        self.initial_lr = initial_lr
        self.step_size = step_size
        self.gamma = gamma
        self.current_epoch = 0
        self.current_lr = initial_lr
    
    def step(self, epoch: Optional[int] = None) -> float:
        """
        Update learning rate for the next epoch
        
        Args:
            epoch: Current epoch number (optional)
        
        Returns:
            Updated learning rate
        """
        if epoch is not None:
            self.current_epoch = epoch
        else:
            self.current_epoch += 1
        
        self.current_lr = self.initial_lr * (self.gamma ** (self.current_epoch // self.step_size))
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class ExponentialLRScheduler:
    """
    Exponential Learning Rate Scheduler
    
    Decays the learning rate exponentially: lr = lr_0 * gamma^epoch
    Provides smooth, continuous decay.
    
    Args:
        initial_lr: Initial learning rate
        gamma: Multiplicative factor of learning rate decay (typically 0.95-0.99)
    """
    
    def __init__(self, initial_lr: float, gamma: float = 0.95):
        self.initial_lr = initial_lr
        self.gamma = gamma
        self.current_epoch = 0
        self.current_lr = initial_lr
    
    def step(self, epoch: Optional[int] = None) -> float:
        """Update learning rate"""
        if epoch is not None:
            self.current_epoch = epoch
        else:
            self.current_epoch += 1
        
        self.current_lr = self.initial_lr * (self.gamma ** self.current_epoch)
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class CosineAnnealingLR:
    """
    Cosine Annealing Learning Rate Scheduler
    
    Sets the learning rate using a cosine annealing schedule:
    lr = lr_min + 0.5 * (lr_max - lr_min) * (1 + cos(pi * epoch / T_max))
    
    Used in modern transformers and state-of-the-art models.
    
    Args:
        initial_lr: Maximum learning rate
        T_max: Maximum number of iterations
        eta_min: Minimum learning rate (default: 0)
    """
    
    def __init__(self, initial_lr: float, T_max: int, eta_min: float = 0):
        self.initial_lr = initial_lr
        self.T_max = T_max
        self.eta_min = eta_min
        self.current_epoch = 0
        self.current_lr = initial_lr
    
    def step(self, epoch: Optional[int] = None) -> float:
        """Update learning rate"""
        if epoch is not None:
            self.current_epoch = epoch
        else:
            self.current_epoch += 1
        
        self.current_lr = self.eta_min + (self.initial_lr - self.eta_min) * \
                         (1 + np.cos(np.pi * self.current_epoch / self.T_max)) / 2
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class CosineAnnealingWarmRestarts:
    """
    Cosine Annealing with Warm Restarts (SGDR)
    
    Implements SGDR: Stochastic Gradient Descent with Warm Restarts.
    Periodically resets the learning rate to help escape local minima.
    
    Args:
        initial_lr: Maximum learning rate
        T_0: Number of iterations for the first restart
        T_mult: Factor to increase T_i after each restart (default: 1)
        eta_min: Minimum learning rate (default: 0)
    """
    
    def __init__(self, initial_lr: float, T_0: int, T_mult: int = 1, eta_min: float = 0):
        self.initial_lr = initial_lr
        self.T_0 = T_0
        self.T_mult = T_mult
        self.eta_min = eta_min
        self.current_epoch = 0
        self.T_cur = 0
        self.T_i = T_0
        self.current_lr = initial_lr
    
    def step(self, epoch: Optional[int] = None) -> float:
        """Update learning rate"""
        if epoch is None:
            epoch = self.current_epoch + 1
        
        self.current_epoch = epoch
        self.T_cur = epoch % self.T_i
        
        # Check if we need to restart
        if self.T_cur == 0 and epoch > 0:
            self.T_i = self.T_i * self.T_mult
        
        self.current_lr = self.eta_min + (self.initial_lr - self.eta_min) * \
                         (1 + np.cos(np.pi * self.T_cur / self.T_i)) / 2
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class OneCycleLR:
    """
    One Cycle Learning Rate Policy
    
    Implements the One Cycle Policy for super-convergence.
    Single cycle: warmup -> peak -> decay
    
    Can significantly reduce training time while improving performance.
    
    Args:
        max_lr: Maximum learning rate
        total_steps: Total number of training steps
        pct_start: Percentage of cycle spent increasing LR (default: 0.3)
        anneal_strategy: 'cos' or 'linear' (default: 'cos')
        div_factor: Initial LR = max_lr / div_factor (default: 25)
        final_div_factor: Final LR = max_lr / final_div_factor (default: 10000)
    """
    
    def __init__(
        self,
        max_lr: float,
        total_steps: int,
        pct_start: float = 0.3,
        anneal_strategy: str = 'cos',
        div_factor: float = 25.0,
        final_div_factor: float = 10000.0
    ):
        self.max_lr = max_lr
        self.total_steps = total_steps
        self.pct_start = pct_start
        self.anneal_strategy = anneal_strategy
        self.initial_lr = max_lr / div_factor
        self.final_lr = max_lr / final_div_factor
        
        self.step_size_up = int(total_steps * pct_start)
        self.step_size_down = total_steps - self.step_size_up
        
        self.current_step = 0
        self.current_lr = self.initial_lr
    
    def step(self) -> float:
        """Update learning rate for next step"""
        self.current_step += 1
        
        if self.current_step <= self.step_size_up:
            # Warmup phase
            pct = self.current_step / self.step_size_up
            self.current_lr = self.initial_lr + (self.max_lr - self.initial_lr) * pct
        else:
            # Annealing phase
            pct = (self.current_step - self.step_size_up) / self.step_size_down
            
            if self.anneal_strategy == 'cos':
                self.current_lr = self.final_lr + (self.max_lr - self.final_lr) * \
                                 (1 + np.cos(np.pi * pct)) / 2
            else:  # linear
                self.current_lr = self.max_lr - (self.max_lr - self.final_lr) * pct
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class ReduceLROnPlateau:
    """
    Reduce Learning Rate on Plateau
    
    Reduces learning rate when a metric has stopped improving.
    Adaptive scheduler based on validation performance.
    
    Args:
        initial_lr: Initial learning rate
        mode: 'min' or 'max' (default: 'min')
        factor: Factor by which LR will be reduced (default: 0.1)
        patience: Number of epochs with no improvement (default: 10)
        threshold: Threshold for measuring improvement (default: 1e-4)
        min_lr: Minimum learning rate (default: 0)
    """
    
    def __init__(
        self,
        initial_lr: float,
        mode: str = 'min',
        factor: float = 0.1,
        patience: int = 10,
        threshold: float = 1e-4,
        min_lr: float = 0
    ):
        self.initial_lr = initial_lr
        self.mode = mode
        self.factor = factor
        self.patience = patience
        self.threshold = threshold
        self.min_lr = min_lr
        
        self.current_lr = initial_lr
        self.best_value = np.inf if mode == 'min' else -np.inf
        self.num_bad_epochs = 0
        self.cooldown_counter = 0
    
    def step(self, metric: float) -> float:
        """
        Update learning rate based on metric
        
        Args:
            metric: Current metric value (e.g., validation loss)
        
        Returns:
            Updated learning rate
        """
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return self.current_lr
        
        # Check if metric improved
        if self.mode == 'min':
            improved = metric < self.best_value - self.threshold
        else:
            improved = metric > self.best_value + self.threshold
        
        if improved:
            self.best_value = metric
            self.num_bad_epochs = 0
        else:
            self.num_bad_epochs += 1
        
        # Reduce LR if no improvement for patience epochs
        if self.num_bad_epochs >= self.patience:
            self.current_lr = max(self.current_lr * self.factor, self.min_lr)
            self.num_bad_epochs = 0
            self.cooldown_counter = self.patience
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class PolynomialLRScheduler:
    """
    Polynomial Learning Rate Decay
    
    Decays learning rate using polynomial function.
    Used in BERT and other transformer models.
    
    Args:
        initial_lr: Initial learning rate
        total_steps: Total number of training steps
        power: Polynomial power (default: 1.0 for linear)
        end_lr: Minimum learning rate (default: 0)
    """
    
    def __init__(
        self,
        initial_lr: float,
        total_steps: int,
        power: float = 1.0,
        end_lr: float = 0
    ):
        self.initial_lr = initial_lr
        self.total_steps = total_steps
        self.power = power
        self.end_lr = end_lr
        self.current_step = 0
        self.current_lr = initial_lr
    
    def step(self) -> float:
        """Update learning rate"""
        self.current_step += 1
        
        if self.current_step >= self.total_steps:
            self.current_lr = self.end_lr
        else:
            decay_factor = (1 - self.current_step / self.total_steps) ** self.power
            self.current_lr = (self.initial_lr - self.end_lr) * decay_factor + self.end_lr
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class LinearWarmupScheduler:
    """
    Linear Warmup Scheduler
    
    Linearly increases learning rate from 0 to target over warmup steps.
    Often combined with other schedulers for stable training start.
    
    Args:
        target_lr: Target learning rate after warmup
        warmup_steps: Number of warmup steps
    """
    
    def __init__(self, target_lr: float, warmup_steps: int):
        self.target_lr = target_lr
        self.warmup_steps = warmup_steps
        self.current_step = 0
        self.current_lr = 0
    
    def step(self) -> float:
        """Update learning rate"""
        self.current_step += 1
        
        if self.current_step >= self.warmup_steps:
            self.current_lr = self.target_lr
        else:
            self.current_lr = self.target_lr * (self.current_step / self.warmup_steps)
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class CyclicalLR:
    """
    Cyclical Learning Rate
    
    Cycles learning rate between base_lr and max_lr.
    Helps explore loss landscape and escape local minima.
    
    Args:
        base_lr: Minimum learning rate
        max_lr: Maximum learning rate
        step_size: Half cycle length (in steps)
        mode: 'triangular', 'triangular2', or 'exp_range'
        gamma: Decay constant for exp_range mode (default: 1.0)
    """
    
    def __init__(
        self,
        base_lr: float,
        max_lr: float,
        step_size: int,
        mode: str = 'triangular',
        gamma: float = 1.0
    ):
        self.base_lr = base_lr
        self.max_lr = max_lr
        self.step_size = step_size
        self.mode = mode
        self.gamma = gamma
        
        self.current_step = 0
        self.cycle = 0
        self.current_lr = base_lr
    
    def step(self) -> float:
        """Update learning rate"""
        self.current_step += 1
        self.cycle = np.floor(1 + self.current_step / (2 * self.step_size))
        x = np.abs(self.current_step / self.step_size - 2 * self.cycle + 1)
        
        if self.mode == 'triangular':
            scale_factor = 1.0
        elif self.mode == 'triangular2':
            scale_factor = 1 / (2 ** (self.cycle - 1))
        else:  # exp_range
            scale_factor = self.gamma ** self.current_step
        
        self.current_lr = self.base_lr + (self.max_lr - self.base_lr) * \
                         max(0, (1 - x)) * scale_factor
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class LRFinder:
    """
    Learning Rate Finder
    
    Finds optimal learning rate by gradually increasing LR and
    monitoring loss. Helps determine good initial learning rate.
    
    Based on Leslie Smith's LR range test.
    
    Args:
        start_lr: Starting learning rate (default: 1e-7)
        end_lr: Ending learning rate (default: 10)
        num_steps: Number of steps for the test (default: 100)
    """
    
    def __init__(
        self,
        start_lr: float = 1e-7,
        end_lr: float = 10,
        num_steps: int = 100
    ):
        self.start_lr = start_lr
        self.end_lr = end_lr
        self.num_steps = num_steps
        
        self.current_step = 0
        self.current_lr = start_lr
        self.lr_history = []
        self.loss_history = []
        
        # Calculate multiplicative factor
        self.mult_factor = (end_lr / start_lr) ** (1 / num_steps)
    
    def step(self, loss: float) -> float:
        """
        Update learning rate and record loss
        
        Args:
            loss: Current training loss
        
        Returns:
            Updated learning rate
        """
        self.lr_history.append(self.current_lr)
        self.loss_history.append(loss)
        
        self.current_step += 1
        self.current_lr = self.start_lr * (self.mult_factor ** self.current_step)
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr
    
    def plot_results(self) -> Tuple[List[float], List[float]]:
        """
        Get LR and loss history for plotting
        
        Returns:
            Tuple of (lr_history, loss_history)
        """
        return self.lr_history, self.loss_history
    
    def suggest_lr(self) -> float:
        """
        Suggest optimal learning rate based on loss curve
        
        Returns:
            Suggested learning rate
        """
        if len(self.loss_history) < 2:
            return self.start_lr
        
        # Find LR with steepest negative gradient
        losses = np.array(self.loss_history)
        lrs = np.array(self.lr_history)
        
        # Smooth losses
        window = min(5, len(losses) // 10)
        if window > 1:
            losses = np.convolve(losses, np.ones(window)/window, mode='valid')
            lrs = lrs[:len(losses)]
        
        # Find steepest descent
        gradients = np.gradient(losses)
        min_gradient_idx = np.argmin(gradients)
        
        # Suggest LR at steepest descent
        suggested_lr = lrs[min_gradient_idx]
        
        return suggested_lr


# ============================================================================
# COMBINED SCHEDULERS
# ============================================================================

class WarmupCosineScheduler:
    """
    Warmup + Cosine Annealing Scheduler
    
    Combines linear warmup with cosine annealing.
    Common in transformer training (BERT, GPT, etc.)
    
    Args:
        max_lr: Maximum learning rate
        warmup_steps: Number of warmup steps
        total_steps: Total number of training steps
        min_lr: Minimum learning rate (default: 0)
    """
    
    def __init__(
        self,
        max_lr: float,
        warmup_steps: int,
        total_steps: int,
        min_lr: float = 0
    ):
        self.max_lr = max_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.min_lr = min_lr
        
        self.current_step = 0
        self.current_lr = 0
    
    def step(self) -> float:
        """Update learning rate"""
        self.current_step += 1
        
        if self.current_step <= self.warmup_steps:
            # Warmup phase
            self.current_lr = self.max_lr * (self.current_step / self.warmup_steps)
        else:
            # Cosine annealing phase
            progress = (self.current_step - self.warmup_steps) / \
                      (self.total_steps - self.warmup_steps)
            self.current_lr = self.min_lr + (self.max_lr - self.min_lr) * \
                             (1 + np.cos(np.pi * progress)) / 2
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_scheduler(
    scheduler_name: str,
    initial_lr: float,
    **kwargs
) -> object:
    """
    Factory function to create scheduler by name
    
    Args:
        scheduler_name: Name of the scheduler
        initial_lr: Initial learning rate
        **kwargs: Additional scheduler-specific arguments
    
    Returns:
        Scheduler instance
    """
    schedulers = {
        'step': StepLRScheduler,
        'exponential': ExponentialLRScheduler,
        'cosine': CosineAnnealingLR,
        'cosine_restarts': CosineAnnealingWarmRestarts,
        'onecycle': OneCycleLR,
        'plateau': ReduceLROnPlateau,
        'polynomial': PolynomialLRScheduler,
        'warmup': LinearWarmupScheduler,
        'cyclical': CyclicalLR,
        'warmup_cosine': WarmupCosineScheduler,
    }
    
    if scheduler_name not in schedulers:
        raise ValueError(f"Unknown scheduler: {scheduler_name}")
    
    return schedulers[scheduler_name](initial_lr, **kwargs)


# ============================================================================
# ALIASES FOR CONVENIENCE
# ============================================================================

step_lr = StepLRScheduler
exp_lr = ExponentialLRScheduler
cosine_lr = CosineAnnealingLR
sgdr = CosineAnnealingWarmRestarts
onecycle = OneCycleLR
plateau_lr = ReduceLROnPlateau
poly_lr = PolynomialLRScheduler
warmup_lr = LinearWarmupScheduler
cyclical_lr = CyclicalLR
lr_finder = LRFinder
warmup_cosine = WarmupCosineScheduler


__all__ = [
    # Scheduler Classes
    'StepLRScheduler',
    'ExponentialLRScheduler',
    'CosineAnnealingLR',
    'CosineAnnealingWarmRestarts',
    'OneCycleLR',
    'ReduceLROnPlateau',
    'PolynomialLRScheduler',
    'LinearWarmupScheduler',
    'CyclicalLR',
    'LRFinder',
    'WarmupCosineScheduler',
    # Utility Functions
    'get_scheduler',
    # Aliases
    'step_lr',
    'exp_lr',
    'cosine_lr',
    'sgdr',
    'onecycle',
    'plateau_lr',
    'poly_lr',
    'warmup_lr',
    'cyclical_lr',
    'lr_finder',
    'warmup_cosine',
]
