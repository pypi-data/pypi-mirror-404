import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.neural_ode import NeuralODELayer

class SimpleDynamics(nn.Module):
        """Simple affine dynamics function f(h, t) = Wh + b"""
        def __init__(self, dim):
            super().__init__()
            self.linear = nn.Linear(dim, dim)
            self.act = nn.Tanh()

        def forward(self, t, x):
            # t is usually concatenated or used in hypernets, 
            # but basic ODE func must accept it.
            return self.act(self.linear(x))

class TestNeuralODELayer:
    """
    Test suite for NeuralODELayer
    Paper: Chen et al., 'Neural Ordinary Differential Equations', NeurIPS 2018.
    """

    @pytest.fixture
    def input_data(self):
        batch_size, dim = 32, 10
        return torch.randn(batch_size, dim, requires_grad=True)

    @pytest.fixture
    def dynamics_func(self):
        return SimpleDynamics(dim=10)

    def test_instantiation_and_shape(self, input_data): # Fixed args to match impl
        model = NeuralODELayer(hidden_dim=10) 
        output = model(input_data)
        assert output.shape == input_data.shape

    def test_numerical_stability(self, input_data, dynamics_func):
        """Ensures solver does not explode into NaNs/Infs for reasonable inputs."""
        model = NeuralODELayer(dynamics_func, torch.tensor([0.0, 5.0])) # Longer integration
        output = model(input_data)
        
        assert torch.isfinite(output).all(), "Output contains NaNs or Infs"

    def test_gradient_propagation_adjoint(self, input_data, dynamics_func):
        """
        Verifies gradients flow to both input and parameters.
        Crucial for Section 2: Adjoint Sensitivity Method.
        """
        model = NeuralODELayer(dynamics_func, torch.tensor([0.0, 1.0]))
        output = model(input_data)
        loss = output.sum()
        loss.backward()

        # Check Input Gradients (Backprop through time/solver)
        assert input_data.grad is not None
        assert torch.isfinite(input_data.grad).all()
        assert input_data.grad.abs().sum() > 0

        # Check Parameter Gradients (Backprop through dynamics network)
        has_grad = False
        for param in dynamics_func.parameters():
            if param.grad is not None:
                has_grad = True
                assert torch.isfinite(param.grad).all()
        assert has_grad, "Dynamics function parameters received no gradients"

    def test_overfitting_simple_task(self, dynamics_func):
        """
        Sanity check: Can it learn an Identity transformation? 
        (y = x is the solution if f(h,t) = 0).
        """
        t = torch.tensor([0.0, 1.0])
        model = NeuralODELayer(dynamics_func, t)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        # Target: Map random noise to itself (Identity)
        x = torch.randn(10, 10)
        target = x.clone()

        initial_loss = float("inf")
        
        for _ in range(50):
            optimizer.zero_grad()
            out = model(x)
            loss = torch.nn.functional.mse_loss(out, target)
            loss.backward()
            optimizer.step()
            
            if initial_loss == float("inf"):
                initial_loss = loss.item()
                
        # Loss should decrease significantly
        assert loss.item() < initial_loss

    def test_time_reversibility_invariant(self, input_data, dynamics_func):
        """
        Paper Invariant: Unique ODE solutions are reversible.
        Integrating forward t0->t1 then backward t1->t0 should recover input.
        Reference: Section 2 (memory efficiency via reversibility).
        """
        t_fwd = torch.tensor([0.0, 1.0])
        t_bwd = torch.tensor([1.0, 0.0])
        
        model_fwd = NeuralODELayer(dynamics_func, t_fwd)
        model_bwd = NeuralODELayer(dynamics_func, t_bwd)
        
        # Forward pass
        h_end = model_fwd(input_data)
        
        # Backward pass (reconstruction)
        h_rec = model_bwd(h_end)
        
        # Check reconstruction error (allow for numerical tolerance of solver)
        error = torch.mean((input_data - h_rec) ** 2)
        assert error < 1e-4, f"Failed to reconstruct input via time reversal. Error: {error}"
