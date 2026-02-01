import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.vision.coord_conv import CoordConv

class TestCoordConv:
    """
    Test suite for CoordConv
    Paper: Liu et al., 'An Intriguing Failing of Convolutional Neural Networks and the CoordConv Solution', NeurIPS 2018.
    """

    @pytest.mark.parametrize("with_r", [True, False])
    def test_pytorch_instantiation_and_shape(self, with_r):
        """
        Verifies output shape matches standard Conv2d expectations 
        despite internal channel concatenation.
        """
        batch, h, w, in_c = 2, 32, 32, 3
        out_c = 16
        kernel_size = 3
        
        # Initialize layer
        model = CoordConv(in_channels=in_c, out_channels=out_c, 
                        kernel_size=kernel_size, with_r=with_r)
        
        x = torch.randn(batch, in_c, h, w)
        out = model(x)
        
        # Standard Conv2d shape logic (assuming padding preserves dim or valid)
        expected_dim = h - (kernel_size - 1) 
        assert out.shape == (batch, out_c, expected_dim, expected_dim)

    def test_pytorch_numerical_stability(self):
        """Checks for NaNs/Infs given valid inputs."""
        model = CoordConv(in_channels=4, out_channels=8, kernel_size=1)
        x = torch.randn(4, 4, 64, 64)
        out = model(x)
        
        assert not torch.isnan(out).any(), "Output contains NaNs"
        assert not torch.isinf(out).any(), "Output contains Infs"

    def test_pytorch_coord_injection_invariant(self):
        """
        Paper Specific Test: 
        Unlike standard Conv2d, CoordConv should produce non-zero output 
        for a zero-input tensor (if bias=False) because coordinate channels 
        provide non-zero information.
        """
        # bias=False ensures standard conv would output pure zeros
        model = CoordConv(in_channels=1, out_channels=1, kernel_size=1, bias=False)
        
        # Initialize weights to non-zero to ensure coordinates are picked up
        nn.init.ones_(model.conv.weight) 
        
        x = torch.zeros(1, 1, 10, 10)
        out = model(x)
        
        # If coordinates are added, the output cannot be all zeros
        assert torch.abs(out).sum() > 0.0, "CoordConv failed to inject coordinate information"

    def test_pytorch_trainability_overfit(self):
        """
        Verifies gradients propagate and the model can learn a simple mapping.
        """
        model = CoordConv(in_channels=1, out_channels=1, kernel_size=1)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()
        
        # Fixed input and target
        x = torch.randn(8, 1, 16, 16)
        target = torch.randn(8, 1, 16, 16)
        
        initial_loss = criterion(model(x), target).item()
        
        # Single training step
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, target)
        loss.backward()
        
        # Check gradient existence
        assert model.conv.weight.grad is not None
        assert torch.abs(model.conv.weight.grad).sum() > 0
        
        optimizer.step()
        
        final_loss = criterion(model(x), target).item()
        assert final_loss < initial_loss, "Loss did not decrease after optimization step"
