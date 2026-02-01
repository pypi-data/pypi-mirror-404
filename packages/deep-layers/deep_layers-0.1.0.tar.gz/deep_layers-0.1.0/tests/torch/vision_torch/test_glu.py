import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.vision.glu import GLU

class TestGLU:
    """
    Test suite for GLU
    Paper: Dauphin et al., 'Language Modeling with Gated Convolutional Networks', ICML 2017.
    """

    @pytest.fixture
    def layer_params(self):
        return {
            "in_channels": 64,
            "out_channels": 64,
            "kernel_size": 3,
            "dilation": 1 # Adjusted based on GLU __init__ args
        }

    def test_instantiation_and_shape(self, layer_params):
        """
        Verifies the layer instantiates and preserves sequence length (N)
        assuming causal padding is implemented as per Sec 2.
        """
        batch_size, seq_len = 4, 20
        model = GLU(**layer_params)
        
        # Input shape: (Batch, In_Channels, Seq_Len)
        x = torch.randn(batch_size, layer_params["in_channels"], seq_len)
        out = model(x)
        
        # Output shape should match length (due to padding) and have correct out_channels
        expected_shape = (batch_size, layer_params["out_channels"], seq_len)
        assert out.shape == expected_shape, f"Expected {expected_shape}, got {out.shape}"

    def test_numerical_stability(self, layer_params):
        """
        Checks for NaNs or Infs during forward pass, which GLUs (linear path)
        should generally avoid better than exp-based units.
        """
        model = GLU(**layer_params)
        x = torch.randn(4, layer_params["in_channels"], 100)
        
        out = model(x)
        
        assert not torch.isnan(out).any(), "Output contains NaNs"
        assert not torch.isinf(out).any(), "Output contains Infs"

    def test_gradient_flow(self, layer_params):
        """
        Verifies gradients exist. Paper Section 3 / Eq (3) emphasizes 
        the linear path allows gradients to flow easily.
        """
        model = GLU(**layer_params)
        x = torch.randn(2, layer_params["in_channels"], 10, requires_grad=True)
        
        out = model(x)
        loss = out.sum()
        loss.backward()
        
        # Check input gradients
        assert x.grad is not None
        # Check weight gradients
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} has no gradient"
                assert not torch.isnan(param.grad).any(), f"Gradient for {name} is NaN"

    def test_causality_invariant(self, layer_params):
        """
        Paper Sec 2: "h_i does not contain information from future words".
        If we change the input at t=K, output at t < K should not change.
        """
        model = GLU(**layer_params)
        model.eval() # Ensure dropout doesn't affect comparison (if present)
        
        seq_len = 10
        x1 = torch.randn(1, layer_params["in_channels"], seq_len)
        x2 = x1.clone()
        
        # Modify the LAST time step in the sequence
        x2[:, :, -1] = torch.randn(1, layer_params["in_channels"])
        
        with torch.no_grad():
            out1 = model(x1)
            out2 = model(x2)
            
        # The output at the FIRST time step should be identical
        # (Assuming causal padding pushes context to the right)
        assert torch.allclose(out1[:, :, 0], out2[:, :, 0], atol=1e-6), \
            "Causality violation: Changing future input affected past output."

    def test_overfit_small_batch(self, layer_params):
        """
        Ensures the layer can learn a simple identity-like mapping.
        """
        torch.manual_seed(42)
        model = GLU(**layer_params)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        # Try to map input to itself (identity)
        x = torch.randn(4, layer_params["in_channels"], 10)
        target = x.clone() # Assuming in_channels == out_channels
        
        initial_loss = nn.MSELoss()(model(x), target).item()
        
        for _ in range(50):
            optimizer.zero_grad()
            out = model(x)
            loss = nn.MSELoss()(out, target)
            loss.backward()
            optimizer.step()
            
        final_loss = loss.item()
        assert final_loss < initial_loss, "Model failed to reduce loss on trivial task"
