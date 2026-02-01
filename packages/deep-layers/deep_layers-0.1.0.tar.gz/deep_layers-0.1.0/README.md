# DeepResearchLayers

![](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![](https://img.shields.io/badge/TensorFlow-FF6F00?logo=tensorflow&logoColor=white)
![](https://img.shields.io/badge/Keras-FF0000?logo=keras&logoColor=white)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)
[![PyPI](https://img.shields.io/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#)
![License](https://img.shields.io/github/license/kuslavicek/deep_layers)
![Version](https://img.shields.io/github/v/release/kuslavicek/deep_layers)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/kuslavicek/deep_layers)


> A Python library for novel and experimental deep learning layers.

`deep_layers` bridges the gap between mathematical theory and usable code, providing "plug-and-play" implementations for PyTorch (and TensorFlow/Keras) of complex layers from research papers.

## Features

### Dual-Backend Compatibility
Supports both **PyTorch** and **TensorFlow** (via `deep_layers/torch` and `deep_layers/tf`).

### Implemented Layers

All layers are available for both **PyTorch** and **TensorFlow**.

#### `deep_layers.vision`
*   **CoordConv** (`coord_conv`): Coordinate Convolution.
*   **DropBlock** (`dropblock`): Structured dropout regularization.
*   **GLU** (`glu`): Gated Linear Unit.
*   **Involution** (`involution`): Inverted convolution.

#### `deep_layers.sequence`
*   **Hyena** (`hyena`): Hyena Hierarchy operator.
*   **Linear Attention** (`linear_attention`): Transformers are RNNs.
*   **Mamba** (`mamba`): Selective State Space Model.
*   **Retention** (`retention`): RetNet layer.

#### `deep_layers.graph`
*   **GCN** (`gcn`): Graph Convolutional Network.
*   **NTN** (`ntn`): Neural Tensor Network.
*   **PointNet** (`pointnet`): PointNet Set Abstraction.
*   **Set Transformer** (`set_transformer`): Permutation-invariant attention.
*   **SGR** (`sgr`): Symbolic Graph Reasoning.

#### `deep_layers.scientific`
*   **CORAL** (`coral`): Coordinate-based Neural Field Operator.
*   **DeepONet** (`deeponet`): Deep Operator Network.
*   **DEQ** (`deq`): Deep Equilibrium Models.
*   **HyperLayer** (`hyperlayer`): HyperNetwork-based dynamic layer.
*   **KAN** (`kan`): Kolmogorov-Arnold Network.
*   **Neural ODE** (`neural_ode`): Ordinary Differential Equation solver layer.
*   **PhyCRNet** (`phycrnet`): Physics-Informed Convolutional-Recurrent.
*   **PirateNet** (`piratenet`): Physics-Informed Residual Adaptive Network.
*   **Sparse Memory** (`sparse_memory`): Differentiable memory with sparse reads/writes.
*   **Steerable Conv** (`steerable_conv`): E(2)-Equivariant Steerable CNN.
*   **VQ** (`vq`): Vector Quantization layer.

## Installation

Install with **PyTorch** support:
```bash
pip install "deep_layers[torch]"
```

Install with **TensorFlow** support:
```bash
pip install "deep_layers[tf]"
```

Install with **both**:
```bash
pip install "deep_layers[all]"
```

For development/editable install:

```bash
git clone https://github.com/yourusername/deep_layers.git
cd deep_layers
pip install -e .
```

## Usage

### PyTorch Example

```python
import torch
from deep_layers.torch.vision import CoordConv

# Initialize layer
layer = CoordConv(in_channels=3, out_channels=64, kernel_size=3)

# Forward pass
x = torch.randn(1, 3, 224, 224)
output = layer(x)
print(output.shape)
```

### TensorFlow Example

```python
import tensorflow as tf
from deep_layers.tf.vision import CoordConv

# Initialize layer
layer = CoordConv(filters=64, kernel_size=3)

# Forward pass
x = tf.random.normal((1, 224, 224, 3))
output = layer(x)
print(output.shape)
```
