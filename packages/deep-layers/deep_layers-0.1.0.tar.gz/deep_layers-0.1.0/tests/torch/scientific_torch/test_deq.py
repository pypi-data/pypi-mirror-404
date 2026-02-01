import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.deq import DEQLayer

class MockFTheta(nn.Module):
        """
        A simple stable transformation f_theta to ensure convergence.
        f(z, x) = tanh(W_z * z + W_x * x)
        Using Tanh helps bound the activation, aiding stability for root finding.
        """
        def __init__(self, hidden_dim, input_dim):
            super().__init__()
            self.linear_z = nn.Linear(hidden_dim, hidden_dim, bias=False)
            self.linear_x = nn.Linear(input_dim, hidden_dim)
            
            # Initialize small weights to ensure contractivity (Lipschitz < 1) for easier convergence
            nn.init.normal_(self.linear_z.weight, std=0.01)
            nn.init.normal_(self.linear_x.weight, std=0.01)

        def forward(self, z, x):
            return torch.tanh(self.linear_z(z) + self.linear_x(x))

class TestDEQLayer:
    """
    Test suite for DEQLayer
    Paper: Bai et al., 'Deep Equilibrium Models', NeurIPS 2019.
    """

    

    @pytest.fixture
    def input_data(self):
        batch, seq_len, input_dim = 4, 10, 8
        return torch.randn(batch, seq_len, input_dim, requires_grad=True)

    @pytest.fixture
    def model(self, input_data):
        _, _, input_dim = input_data.shape
        hidden_dim = 8
        # Call MockFTheta directly (it is in global scope)
        f_theta = MockFTheta(hidden_dim, input_dim)
        return DEQLayer(f_theta)


    # --- Tests ---

    def test_instantiation_and_shape(self, model, input_data):
        """
        Verifies the layer outputs the equilibrium sequence with the correct shape.
        Paper Eq (2): z* = f(z*; x)
        """
        z_star = model(input_data)
        
        assert z_star.shape == (input_data.shape[0], input_data.shape[1], 8)
        assert not torch.isnan(z_star).any(), "Output contains NaNs"
        assert not torch.isinf(z_star).any(), "Output contains Infs"

    def test_fixed_point_invariant(self, model, input_data):
        """
        Paper Core Concept: The output must be the fixed point of the internal layer.
        Check: || f_theta(z*, x) - z* || ≈ 0
        """
        z_star = model(input_data)
        
        # Manually apply the internal cell one more time
        # Note: Accessing internal cell via model.cell or similar attribute assumed
        f_z_star = model.cell(z_star, input_data)
        
        # The difference should be within the solver's tolerance
        diff = torch.norm(f_z_star - z_star)
        assert diff.item() < 2e-2, f"Output is not an equilibrium point. Diff: {diff.item()}"

    def test_gradient_existence_implicit_differentiation(self, model, input_data):
        """
        Paper Theorem 1: Implicit Differentiation.
        Ensures gradients propagate through the equilibrium point without
        storing intermediate states of the solver (autograd check).
        """
        z_star = model(input_data)
        loss = z_star.sum()
        loss.backward()

        # Check gradients on input
        assert input_data.grad is not None
        assert torch.norm(input_data.grad) > 0

        # Check gradients on weights (inside the internal cell)
        param = list(model.cell.parameters())[0]
        assert param.grad is not None
        assert torch.norm(param.grad) > 0

    def test_batch_independence(self, model):
        """
        Ensures that the root finding in one batch element doesn't affect others.
        """
        # Create two identical inputs
        x1 = torch.randn(1, 5, 8)
        x2 = x1.clone()
        
        # Create a different input
        x3 = torch.randn(1, 5, 8)
        
        # Batch them: [x1, x3] and [x2, x3]
        batch_a = torch.cat([x1, x3], dim=0)
        batch_b = torch.cat([x2, x3], dim=0)
        
        out_a = model(batch_a)
        out_b = model(batch_b)
        
        # The output corresponding to x1 and x2 should be identical
        assert torch.allclose(out_a[0], out_b[0], atol=1e-5)

    def test_overfit_synthetic_task(self):
        """
        Trainability Sanity Check.
        Can the DEQ learn a simple identity mapping?
        Target: Output should match Input (approx).
        """
        dim = 4
        f_theta = MockFTheta(dim, dim)
        model = DEQLayer(f_theta)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        # Random input
        x = torch.randn(16, 5, dim, requires_grad=True) 
        target = torch.tanh(x).detach()
        
        for _ in range(50):
            optimizer.zero_grad()
            output = model(x)
            loss = nn.MSELoss()(output, target)
            loss.backward()
            optimizer.step()
            
        assert loss.item() < 0.1, "Model failed to converge on trivial task"
