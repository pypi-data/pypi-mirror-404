# AdaptiveCycleLR

Loss-aware learning rate scheduler for PyTorch.

## Overview

Standard schedulers (StepLR, CosineAnnealing, OneCycleLR) follow predetermined schedules regardless of training dynamics. AdaptiveCycleLR monitors loss trends in real-time and adjusts the learning rate accordingly.

The scheduler operates in three phases:
- **Exploit**: Low LR when loss is decreasing steadily
- **Explore**: Medium LR with noise when loss plateaus  
- **Escape**: High LR burst when stuck in local minima

## Installation

```bash
pip install adaptive-cycle-lr
```

Or install from source:

```bash
git clone https://github.com/yourusername/adaptive-cycle-lr
cd adaptive-cycle-lr
pip install -e .
```

## Usage

```python
from adaptive_cycle_lr import AdaptiveCycleLR

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
scheduler = AdaptiveCycleLR(
    optimizer,
    base_lr=1e-4,
    max_lr=1e-3,
    window_size=150,
    patience=600
)

for epoch in range(epochs):
    for batch in dataloader:
        loss = train_step(batch)
        optimizer.step()
        
        info = scheduler.step(loss.item())
        # info contains: lr, phase, improvement, etc.
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_lr` | 1e-4 | Minimum learning rate |
| `max_lr` | 1e-3 | Maximum learning rate |
| `window_size` | 150 | Steps for trend analysis |
| `patience` | 600 | Steps before escape trigger |
| `improvement_threshold` | 0.01 | Threshold for exploit phase |
| `plateau_threshold` | 0.005 | Threshold for explore phase |
| `smoothing` | 0.99 | LR change smoothing factor |
| `escape_multiplier` | 1.5 | LR multiplier during escape |

## Benchmark

Comparison on speech synthesis task (600 epochs, batch size 128):

| Scheduler | Final Loss | Best Loss | Convergence |
|-----------|------------|-----------|-------------|
| OneCycleLR | 0.446 | 0.446 | Epoch 570 |
| AdaptiveCycleLR | 0.427 | 0.427 | Epoch 540 |

AdaptiveCycleLR achieved 4% lower loss and converged 30 epochs faster.

## How It Works

```
Loss decreasing → EXPLOIT (low LR, fine-tune)
     ↓
Loss plateaus → EXPLORE (medium LR + noise, search)
     ↓
Loss increasing → ESCAPE (high LR burst, jump out)
     ↓
Loss decreasing → back to EXPLOIT
```

The scheduler maintains a sliding window of recent losses and computes the improvement rate:

```
improvement = (old_avg - recent_avg) / old_avg
```

Phase transitions are smoothed to prevent oscillation.

## State Management

```python
# Save
state = scheduler.state_dict()
torch.save(state, 'scheduler.pt')

# Load
scheduler.load_state_dict(torch.load('scheduler.pt'))
```

## Requirements

- Python >= 3.7
- PyTorch >= 1.9

## License

MIT

## Citation

```bibtex
@software{adaptive_cycle_lr,
  title={AdaptiveCycleLR: Loss-aware Learning Rate Scheduling},
  year={2026},
  url={https://github.com/yourusername/adaptive-cycle-lr}
}
```
