
import pytest
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
import random
import numpy as np

@pytest.fixture(scope="session", autouse=True)
def set_global_seeds():
    if HAS_TORCH:
        torch.manual_seed(0)
    random.seed(0)
    np.random.seed(0)

@pytest.fixture(params=["cpu", "cuda"])
def device(request):
    if not HAS_TORCH:
        pytest.skip("Torch not available")
    if request.param == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    return torch.device(request.param)
