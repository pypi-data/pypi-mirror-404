# torchinspect

Lightweight utilities for inspecting PyTorch model shapes and common mismatch errors.

## Install

From PyPI (recommended):

```bash
pip install torch_model_inspector
```

Local editable install (for development):

```bash
pip install -e .
```

## Usage

```python
import torch
import torch.nn as nn
from torchinspect import analyze, count_parameters, print_report

class BadModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 8, kernel_size=3, stride=1, padding=1)
        self.fc = nn.Linear(16, 10)  # intentionally wrong

    def forward(self, x):
        x = self.conv(x)
        return self.fc(x)

m = BadModel()
x = torch.randn(2, 3, 32, 32)

res = analyze(m, x)
print_report(res, last_n=20)

total_params = count_parameters(m)
print("trainable params:", total_params)
```

## What’s included

- `analyze(model, *example_inputs)`: records per-layer input/output shapes
- `print_report(result)`: prints a readable summary
- `suggest_fixes(records, error)`: helpful hints for common shape issues
- `count_parameters(model, trainable_only=True)`: total parameter count

## Import name

The PyPI package is `torch_model_inspector`, but you import it as:

```python
import torchinspect
```

## License

MIT
