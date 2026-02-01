# DeepResearchLayers

A library implementing novel deep learning layers from research papers.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
import torch
from deep_layers.torch.vision import CoordConv

layer = CoordConv(in_channels=3, out_channels=16)
x = torch.randn(1, 3, 32, 32)
y = layer(x)
```

## Project Structure

- `core/`: Shared utilities.
- `torch/`: PyTorch implementations.
    - `vision/`: Vision layers (CoordConv, Involution, etc.).
    - `sequence/`: Sequence models (Mamba, RetNet, etc.).
    - `graph/`: Graph layers (GCN, GraphonConv, etc.).
    - `scientific/`: SciML and Operator Learning layers (DeepONet, KAN, etc.).
- `tf/`: TensorFlow implementations.
