# TrainWatch 🔍

**Your PyTorch training is hiding problems. Here's what you're missing:**

- 🐌 GPU sitting idle while DataLoader struggles
- 💾 Memory leaking 100MB per epoch
- 📈 Loss about to explode (but you'll only know in 2 hours)

**TrainWatch shows you in real-time. One line of code.**

---

## Quick Start

```bash
pip install trainwatch
```

```python
from trainwatch import Watcher

watcher = Watcher()

for epoch in range(epochs):
    for images, labels in dataloader:
        loss = train_step(images, labels)
        watcher.step(loss=loss.item())
    
    watcher.epoch_end()
```

**That's it.** You now see:
- Step timing
- Loss trends (moving average)
- CPU/RAM usage
- GPU VRAM tracking
- Real-time warnings

---

## Example Output

```
Step     10 | loss=2.3045 | time=0.234s | CPU=45.2% | RAM=23.1% | VRAM=1024MB
Step     20 | loss=2.1234 | time=0.231s | CPU=46.1% | RAM=23.4% | VRAM=1025MB
Step     30 | loss=1.9876 | time=0.229s | CPU=44.8% | RAM=23.6% | VRAM=1026MB
⚠️  WARNING: Loss variance spike detected - training may be unstable
Step     40 | loss=2.5432 | time=0.235s | CPU=45.5% | RAM=23.8% | VRAM=1027MB

============================================================
Epoch 1 Summary:
  Loss (avg): 2.1204 [decreasing]
  VRAM delta: +3.2MB
============================================================
```

---

## Configuration

```python
watcher = Watcher(
    window=20,               # Moving average window (default: 20)
    print_every=10,          # Print every N steps (default: 10)
    show_gpu=True,           # Show GPU metrics (default: True)
    warn_on_leak=True,       # Warn on memory leaks (default: True)
    warn_on_bottleneck=True, # Warn on DataLoader issues (default: True)
    warn_on_variance=True,   # Warn on loss spikes (default: True)
    device='cuda:0'          # GPU device (default: 'cuda:0')
)
```

---

## What It Watches

| Metric | What It Tells You |
|--------|-------------------|
| **Step Time** | How fast your training loop runs |
| **Loss (Moving Avg)** | Smoothed loss trend, easier to read than raw loss |
| **Loss Variance** | Detects training instability before it crashes |
| **CPU/RAM** | System load - high RAM often means DataLoader issues |
| **GPU VRAM** | Memory usage - tracks leaks across epochs |
| **VRAM Delta** | Memory increase per epoch - positive = leak |

---

## Warnings

TrainWatch gives you 3 critical warnings:

### 🔴 Loss Variance Spike
Your loss is jumping around wildly. Training might diverge.

**Likely cause:** Learning rate too high, bad batch, or data issue

### 🔴 Memory Leak
VRAM increasing +50MB per epoch.

**Likely cause:** Tensors not released, gradients accumulating, or Python refs

### 🔴 DataLoader Bottleneck
GPU idle while waiting for data.

**Likely cause:** `num_workers=0`, slow data augmentation, or I/O issues

---

## When to Use TrainWatch

✅ **Use it when:**
- Training a new model for the first time
- Debugging slow or unstable training
- Running long experiments overnight
- Want peace of mind your training is healthy

❌ **Don't need it when:**
- Training is working perfectly (lucky you!)
- You're using WandB/TensorBoard for detailed logging
- You want fancy visualizations (we're CLI-only for now)

---

## What TrainWatch Doesn't Do

- **No cloud required** - everything runs locally
- **No fancy UI** - just clean terminal output
- **No metric logging** - just real-time monitoring (v0.2 will add CSV export)
- **No distributed training** - single GPU only for now

---

## Examples

See the [`examples/`](examples/) directory for complete working examples:

### 🎯 Simple CNN - CIFAR-10
Perfect for getting started. Shows basic TrainWatch integration with a simple 2-layer CNN.

```bash
python examples/cifar10_simple.py
```

**Tested on:** Kaggle CPU, GPU T4, GPU P100  
**Training time:** ~2 min (GPU)  
**Results:** [examples/cifar10_results.md](examples/cifar10_results.md)

### 🏗️ DenseNet121 - CIFAR-10 🆕
Real PyTorch model from torchvision.models, training from scratch.

```bash
python examples/densenet_cifar10.py
```

**Model:** DenseNet121 (weights=None, ~7M params)  
**Image size:** 224×224 (CIFAR resized)  
**VRAM:** ~850MB  
**Shows:** Production architecture, gradient clipping

### 🚀 Advanced ResNet - Fashion-MNIST  
Production-ready example with ResNet-18, data augmentation, and LR scheduling.

```bash
python examples/resnet_fashion_mnist.py
```

**Model:** 11M parameters  
**Training time:** ~5 min (GPU)

### 🐛 Memory Leak Detection - CIFAR-10 ⚠️
Interactive demo showing memory leak detection in action.

```bash
python examples/memory_leak_demo.py
```

**Shows:** Intentional leak vs correct implementation  
**TrainWatch warns:** Memory leak detected automatically!

👉 **Full examples documentation:** [examples/README.md](examples/README.md)

---

## 📊 Test Results & Benchmarks

All examples tested on Kaggle with real GPUs. Full results in [`examples/*_results.md`](examples/).

### Performance Summary

| Example | GPU | Step Time | Accuracy | VRAM | Notes |
|---------|-----|-----------|----------|------|-------|
| **Simple CNN** | T4 | ~5ms | 75% | 25MB | 12x faster than CPU |
| | P100 | ~4ms | 75% | 25MB | 15x faster than CPU |
| **DenseNet121** | T4 | 331ms | 81.76% | 115MB | 224×224 images |
| | P100 | 175ms | 82.15% | 115MB | **1.9x faster than T4** |
| **ResNet-18** | T4 | 85ms | 92.28% | 147MB | Fashion-MNIST |
| | P100 | 47ms | 91.86% | 148MB | **1.8x faster than T4** |
| **Memory Leak** | Both | - | - | +1.2MB | **Leak detected!** ⚠️ |

### Key Findings

✅ **TrainWatch Overhead:** <1ms per step (negligible)  
✅ **Memory Leak Detection:** Perfect - caught +1.2MB leak in 3 epochs  
✅ **VRAM Tracking:** Accurate across all models (25MB - 4GB range)  
✅ **Cross-GPU Consistency:** Identical behavior on T4 and P100  
✅ **No False Positives:** 0 false alarms on healthy training runs

### Kaggle Test Collection

🔗 **Try it yourself:** [TrainWatch Examples on Kaggle](https://www.kaggle.com/collections/trainwatch-examples)

All examples ready to run with one click! Includes:
- Simple CNN (CPU, T4, P100 tested)
- DenseNet121 (production model)
- ResNet-18 (Fashion-MNIST)
- Memory Leak Demo (educational)

---

## Requirements

- Python 3.8+
- PyTorch 1.9+
- psutil
- numpy

---

## Installation

From PyPI:
```bash
pip install trainwatch
```

From source (for development):
```bash
git clone https://github.com/Hords01/trainwatch.git
cd trainwatch
pip install -e .  # Editable install
```

---

## Examples

See `examples/cifar10_demo.py` for a complete working example.

---

## Contributing

Found a bug? Have a feature request? 

Open an issue or PR on [GitHub](https://github.com/Hords01/trainwatch)

---

## Author

**Emirkan Beyaz**

- 📧 Email: [emirkanbeyaz01@gmail.com](mailto:emirkanbeyaz01@gmail.com)
- 💼 LinkedIn: [linkedin.com/in/emirkan-beyaz-07732933b](https://www.linkedin.com/in/emirkan-beyaz-07732933b)
- 🔗 GitHub: [@Hords01](https://github.com/Hords01)

Built with ❤️ for the PyTorch community

---

## License

MIT License - see LICENSE file

---

## Why TrainWatch?

Because watching `loss=2.3456` scroll by for 3 hours, only to find out your DataLoader was the bottleneck all along, is painful.

**TrainWatch catches problems while you can still fix them.**