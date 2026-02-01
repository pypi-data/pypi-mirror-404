import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.kan import KANLayer

class TestKANLayer:
    """
    Test suite for KANLayer
    Paper: Liu et al., 'KAN: Kolmogorov-Arnold Networks', arXiv:2404.19756 (April 2024).
    """

    @pytest.mark.parametrize("in_features, out_features", [(3, 5), (10, 1), (1, 10)])
    @pytest.mark.parametrize("grid_size", [5, 10])
    def test_instantiation_and_shapes(self, in_features, out_features, grid_size):
        """
        Verifies that the layer instantiates and outputs correct shapes.
        Reference: Eq (2.5) - Summation of phi_l,j,i
        """
        batch_size = 16
        model = KANLayer(in_features, out_features, grid_size=grid_size)
        
        input_tensor = torch.randn(batch_size, in_features)
        output = model(input_tensor)
        
        assert output.shape == (batch_size, out_features)
        assert not torch.isnan(output).any(), "Forward pass produced NaNs"
        assert not torch.isinf(output).any(), "Forward pass produced Infs"

    def test_parameter_scaling_with_grid(self):
        """
        Reference: Section 2.2 & Parameter Count
        Parameters should increase with grid size G. 
        Unlike MLPs, KAN weights depend on grid intervals.
        """
        in_dim, out_dim = 4, 4
        model_small = KANLayer(in_dim, out_dim, grid_size=3)
        model_large = KANLayer(in_dim, out_dim, grid_size=10)
        
        params_small = sum(p.numel() for p in model_small.parameters())
        params_large = sum(p.numel() for p in model_large.parameters())
        
        assert params_large > params_small, "Increasing grid size should increase parameter count (spline coefficients)."

    def test_gradient_flow(self):
        """
        Verifies that gradients flow to the spline coefficients.
        Reference: Section 2.2 - Back propagation is possible.
        """
        model = KANLayer(in_features=2, out_features=1)
        x = torch.randn(4, 2, requires_grad=True)
        target = torch.randn(4, 1)
        
        output = model(x)
        loss = nn.MSELoss()(output, target)
        loss.backward()

        # Check input gradients (verifies differentiability wrt input)
        assert x.grad is not None
        
        # Check parameter gradients (verifies learnability of splines)
        has_grad = False
        for param in model.parameters():
            if param.grad is not None and param.grad.abs().sum() > 0:
                has_grad = True
                break
        assert has_grad, "No gradients flowing to KAN parameters"

    def test_overfitting_toy_function(self):
        """
        Reference: Section 3.1 - Toy Datasets.
        A simple KAN layer should easily fit y = x^2 + bias.
        """
        torch.manual_seed(42)
        # Simple 1D regression: y = x^2
        X = torch.rand(100, 1) * 2 - 1  # Range [-1, 1]
        y = X ** 2
        
        # Use a slightly larger grid to ensure expressivity
        model = KANLayer(in_features=1, out_features=1, grid_size=5, spline_order=3)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        losses = []
        for _ in range(500):
            optimizer.zero_grad()
            pred = model(X)
            loss = nn.MSELoss()(pred, y)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            
        # Check convergence
        assert losses[-1] < 0.05, f"Failed to overfit simple quadratic function. Final loss: {losses[-1]}"

    def test_spline_update_grid_logic(self):
        """
        Splines are defined on bounded regions. Inputs outside [-1, 1] (or grid range)
        should still be handled (usually via grid extension or valid extrapolation).
        """
        model = KANLayer(in_features=1, out_features=1)
        
        # Pass an input significantly outside standard initialization range
        large_input = torch.tensor([[10.0]]) 
        
        try:
            out = model(large_input)
        except Exception as e:
            pytest.fail(f"Layer crashed on out-of-distribution input: {e}")
        
        assert not torch.isnan(out).any()
