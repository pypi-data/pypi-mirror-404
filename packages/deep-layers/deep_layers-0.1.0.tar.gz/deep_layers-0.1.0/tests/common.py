
import torch

def assert_no_nan_inf(x, name="tensor"):
    assert torch.isfinite(x).all(), f"{name} contains NaN or Inf"
