"""
TrainWatch - PyTorch training monitor with one line of code
"""
import time
from typing import Optional
from .system import SystemMonitor
from .metrics import LossTracker


class Watcher:
    """
    Monitor PyTorch training health in real-time

    Tracks:
    - Loss trends (moving average, variance)
    - Step/epoch timing
    - CPU and RAM usage
    - GPU VRAM usage and leaks
    - DataLoader bottlenecks

    Example:
        >>> watcher = Watcher()
        >>> for epoch in range(epochs):
        ...   for images, labels in dataloader:
        ...       loss = train_step(images, labels)
        ...       watcher.step(loss=loss.item())
        ...   watcher.epoch_end()
    """

    def __init__(
        self,
        window: int = 20,
        print_every: int = 10,
        show_gpu: bool = True,
        warn_on_leak: bool = True,
        warn_on_bottleneck: bool = True,
        warn_on_variance: bool = True,
        device: str = 'cuda:0'
    ):
        """
        Initialize training watcher

        Args:
            window: Number of recent steps to keep for moving averages
            print_every: Print metrics every N steps
            show_gpu: Show GPU VRAM metrics
            warn_on_leak: Warn about potential memory leaks
            warn_on_bottleneck: Warn about DataLoader bottlenecks
            warn_on_variance: Warn about loss variance spikes
            device: CUDA device to monitor (e.g., 'cuda:0')
        """
        self.window = window
        self.print_every = print_every
        self.show_gpu = show_gpu
        self.warn_on_leak = warn_on_leak
        self.warn_on_bottleneck = warn_on_bottleneck
        self.warn_on_variance = warn_on_variance

        # core components
        self.loss_tracker = LossTracker(window=window)
        self.system_monitor = SystemMonitor(device=device)

        # timing
        self.step_count = 0
        self.epoch_count = 0
        self.last_step_time = time.time()
        self.epoch_start_time: Optional[float] = None

        # baselines (set at end of first epoch)
        self.baselines_set = False

    def step(self, loss: float) -> None:
        """
        Record a training step

        Args:
            loss: Loss value for this step (scalar)
        """
        self.step_count += 1

        # timing
        now = time.time()
        step_time = now - self.last_step_time
        self.last_step_time = now

        # track loss
        self.loss_tracker.add(loss)

        # should we print?
        if self.step_count % self.print_every != 0:
            return

        # get metrics
        metrics = self.system_monitor.get_metrics()
        loss_avg = self.loss_tracker.get_moving_average()

        # build message
        msg = f"Step {self.step_count:>6} | "

        if loss_avg is not None:
            msg += f"loss={loss_avg:.4f} | "
        else:
            msg += f"loss={loss:.4f} | "

        msg += f"time={step_time:.3f}s | "
        msg += f"CPU={metrics['cpu_percent']:.1f}% | "
        msg += f"RAM={metrics['ram_percent']:.1f}%"

        if self.show_gpu and 'vram_mb' in metrics:
            msg += f" | VRAM={metrics['vram_mb']:.0f}MB"

        print(msg)

        # warnings (only after baselines are set)
        if self.baselines_set:
            self._check_warnings(step_time, metrics)

    def epoch_end(self) -> None:
        """Call at the end of each epoch for summary and baseline setting"""
        self.epoch_count += 1

        # first epoch: set baselines
        if not self.baselines_set and self.epoch_count == 1:
            self.system_monitor.set_vram_baseline()
            self.loss_tracker.set_variance_baseline()
            self.baselines_set = True
            print(f"✓ Epoch {self.epoch_count} complete - baselines set")
            return

        # epoch summary
        loss_avg = self.loss_tracker.get_moving_average()
        trend = self.loss_tracker.get_trend()

        msg = f"\n{'='*60}\n"
        msg += f"Epoch {self.epoch_count} Summary:\n"

        if loss_avg is not None:
            msg += f"   Loss (avg): {loss_avg:.4f}"
            if trend:
                msg += f" [{trend}]"
            msg += "\n"

        # VRAM delta
        if self.show_gpu:
            vram_delta = self.system_monitor.get_vram_delta()
            if vram_delta is not None:
                msg += f"   VRAM delta: {vram_delta:+.1f}MB\n"

        msg += f'='*60
        print(msg)

        # check for memory leak
        if self.warn_on_leak and self.show_gpu:
            vram_delta = self.system_monitor.get_vram_delta()
            if vram_delta is not None and vram_delta > 50: # > 50MB increase
                print(f"⚠️  WARNING: Possible memory leak (+{vram_delta:.0f}MB VRAM since baseline)")

    def _check_warnings(self, step_time: float, metrics: dict) -> None:
        """Check for warning conditions"""

        # variance spike
        if self.warn_on_variance:
            if self.loss_tracker.detect_variance_spike():
                print("⚠️  WARNING: Loss variance spike detected - training may be unstable")

        # DataLoader bottlenect
        if self.warn_on_bottleneck and self.show_gpu:
            # simple heuristic: if GPU VRAM is allocated but step is slow
            if 'vram_mb' in metrics and metrics['vram_mb'] > 100: # GPU is being used
                if step_time > 0.5: # but step is slow
                    if metrics['cpu_percent'] < 50: # and CPU is idle
                        print("⚠️  WARNING: Possible DataLoader bottleneck (slow steps, idle CPU)")




