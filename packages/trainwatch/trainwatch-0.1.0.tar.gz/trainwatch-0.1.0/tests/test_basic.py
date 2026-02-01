"""
Basic tests for TrainWatch
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import torch
from trainwatch import Watcher


def test_watcher_initialization():
    """Test that Watcher can be initialized"""
    watcher = Watcher()
    assert watcher is not None
    assert watcher.step_count == 0
    assert watcher.epoch_count == 0
    print("✓ Watcher initialization test passed")

def test_watcher_step():
    """Test that step() works without errors"""
    watcher = Watcher(print_every=1)

    #simulate some training steps
    for i in range(10):
        watcher.step(loss=2.0 - i * 0.1)

    assert watcher.step_count == 10
    print("✓ Watcher step test passed")

def test_watcher_epoch():
    """Test epoch_end() functionality"""
    watcher = Watcher(print_every=5)

    # simulate one epoch
    for i in range(20):
        watcher.step(loss=2.0 - i * 0.05)

    watcher.epoch_end()
    assert watcher.epoch_count == 1
    print("✓ Watcher epoch test passed")

def test_loss_tracker():
    """Test loss tracking and moving average"""
    from trainwatch.metrics import LossTracker

    tracker = LossTracker(window=10)

    # add some losses
    for i in range(15):
        tracker.add(2.0 -i * 0.1)

    avg = tracker.get_moving_average()
    assert avg is not None
    assert 0.5 < avg < 1.5 # should be around 1.0

    print("✓ Loss tracker test passed")

def test_system_monitor():
    """Test system monitoring"""
    from trainwatch.system import SystemMonitor

    monitor = SystemMonitor()
    metrics = monitor.get_metrics()

    assert 'cpu_percent' in metrics
    assert 'ram_percent' in metrics
    assert 0 <= metrics['cpu_percent'] <= 100
    assert 0 <= metrics['ram_percent'] <= 100

    if torch.cuda.is_available():
        assert 'vram_mb' in metrics
        assert metrics['vram_mb'] >= 0

    print("✓ System monitor test passed")

def test_full_training_simulation():
    """Test full training simulation"""
    watcher = Watcher(print_every=10, show_gpu=torch.cuda.is_available())

    # simulate 2 epochs of training
    for epoch in range(2):
        for step in range(50):
            # decreasing loss
            loss = 2.0 - (epoch * 50 + step) * 0.01
            watcher.step(loss=loss)

        watcher.epoch_end()

    assert watcher.step_count == 100
    assert watcher.epoch_count == 2
    print("✓ Full training simulation test passed")


if __name__ == "__main__":
    print("Running TrainWatch tests...\n")

    test_watcher_initialization()
    test_watcher_step()
    test_watcher_epoch()
    test_loss_tracker()
    test_system_monitor()
    test_full_training_simulation()

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


