"""
System metrics collection for CPU, RAM, and GPU VRAM
"""

import psutil
import torch
from typing import Dict, Optional

class SystemMonitor:
    """Monitor system resources (CPU, RAM, GPU VRAM)"""

    def __init__(self, device: str = 'cuda:0'):
        """
        Initialize system monitor

        Args:
            device: CUDA device to monitor (e.g., 'cuda:0')
        """
        self.device = device
        self.has_gpu = torch.cuda.is_available()

        psutil.cpu_percent(interval=None)

        self.vram_baseline: Optional[float] = None

    def get_metrics(self) -> Dict[str, float]:
        """
        Get current system metrics

        Returns:
            Dictionary with cpu_percent, ram_percent, and optionally vram_mb
        """
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'ram_percent': psutil.virtual_memory().percent,
        }

        if self.has_gpu:
            vram_bytes = torch.cuda.memory_allocated(self.device)
            metrics['vram_mb'] = vram_bytes / (1024 ** 2)

        return metrics

    def set_vram_baseline(self) -> None:
        """Set current VRAM usage as baseline for leak detection"""
        if self.has_gpu:
            self.vram_baseline = torch.cuda.memory_allocated(self.device) / (1024 ** 2)

    def get_vram_delta(self) -> Optional[float]:
        """
        Get VRAM increase from baseline

        Returns:
            VRAM delta in MB, or None if baseline not set
        """
        if not self.has_gpu or self.vram_baseline is None:
            return None

        current = torch.cuda.memory_allocated(self.device) / (1024 ** 2)
        return current - self.vram_baseline

    def detect_dataloader_bottleneck(self, gpu_util: float, step_time: float) -> bool:
        """
        Detect if DataLoader is bottlenecking training

        Simple heuristic: if step time is high but GPU utilization is low, likely waiting for data

        Args:
            gpu_util: PU utilization percentage (0-100)
            step_time: Time taken for this step in seconds

        Returns:
            True if bottleneck detected
        """
        # if step takes > 0.5s but GPU is < 50% utilized
        return step_time > 0.5 and gpu_util < 50.0



