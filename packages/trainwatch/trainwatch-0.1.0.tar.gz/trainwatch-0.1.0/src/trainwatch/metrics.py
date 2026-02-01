"""
Loss metrics and trend analysis
"""

import numpy as np
from collections import deque
from typing import Optional


class LossTracker:
    """Track and analyze loss behavior during training"""

    def __init__(self, window: int = 20):
        """
        Initialize loss tracker

        Args:
            window: Number of recent losses to keep for analysis
        """
        self.window = window
        self.losses = deque(maxlen=window)
        self.variance_baseline: Optional[float] = None

    def add(self, loss: float) -> None:
        """Add a new loss value"""
        self.losses.append(loss)

    def get_moving_average(self) -> Optional[float]:
        """
        Calculate moving average of recent losses

        Returns:
            Moving average, or None if insufficient data
        """
        if len(self.losses) < 5:
            return None
        return float(np.mean(self.losses))

    def get_variance(self) -> Optional[float]:
        """
        Calculate variance of recent losses

        Returns:
            Variance, or None if insufficient data
        """
        if len(self.losses) < 10:
            return None
        return float(np.var(self.losses))

    def set_variance_baseline(self) -> None:
        """set current variance as baseline for comparison"""
        variance = self.get_variance()
        if variance is not None:
            self.variance_baseline = variance

    def detect_variance_spike(self, threshold: float = 5.0) -> bool:
        """
        Detect if loss variance has spiked significantly

        Args:
            threshold: Multiplier for variance spike (e.g., 5x baseline)

        Returns:
            True if variance spike detected
        """
        if self.variance_baseline is None:
            return False

        current_var = self.get_variance()
        if current_var is None:
            return False

        if self.variance_baseline < 1e-8:
            return False

        return current_var > (self.variance_baseline * threshold)

    def get_trend(self) -> Optional[str]:
        """
        Determine loss trend (decreasing, stable, increasing)

        Returns:
            'decreasing', 'stable', 'increasing', or None if insufficient data
        """
        if len(self.losses) < 10:
            return None

        losses_array = np.array(self.losses)
        mid = len(losses_array) // 2

        first_half_mean = np.mean(losses_array[:mid])
        second_half_mean = np.mean(losses_array[mid:])

        diff = second_half_mean - first_half_mean

        # use relative threshold (5% of first half mean)
        threshold = 0.05 * abs(first_half_mean) if first_half_mean != 0 else 0.01

        if diff < -threshold:
            return 'decreasing'
        elif diff > threshold:
            return 'increasing'
        else:
            return 'stable'



















