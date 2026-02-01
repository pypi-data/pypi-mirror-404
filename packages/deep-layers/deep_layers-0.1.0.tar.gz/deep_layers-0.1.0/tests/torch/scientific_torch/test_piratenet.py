import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.piratenet import PirateNetBlock

class TestPirateNet:
    """
    Test suite for PirateNet
    Paper: Krishnapriyan et al., 'PirateNets: Physics-informed Deep Learning with Residual Adaptive Networks', JMLR 2024.
    """

    @pytest.fixture
    def input_dim(self):
        return 64

    @pytest.fixture
    def batch_size(self):
        return 16

    @pytest.fixture
    def model(self, input_dim):
        # Implementation should accept dimension and activation
        return PirateNetBlock(units=input_dim, activation='tanh') # Fixed arg name

    @pytest.fixture
    def data(self, batch_size, input_dim):
        # x: current layer input, U/V: gating vectors from embedding
        x = torch.randn(batch_size, input_dim)
        U = torch.randn(batch_size, input_dim)
        V = torch.randn(batch_size, input_dim)
        return x, U, V

    def test_instantiation_and_shape(self, model, data):
        """
        Verifies the layer instantiates and preserves shape (Residual property).
        """
        x, U, V = data
        output = model(x, U, V)
        
        assert output.shape == x.shape, \
            f"Output shape {output.shape} mismatch. Expected {x.shape}"
        assert not torch.isnan(output).any(), "Output contains NaNs"
        assert not torch.isinf(output).any(), "Output contains Infs"

    def test_initialization_invariant_identity(self, model, data):
        """
        CRITICAL PAPER TEST (Section 4, Eq 4.6 & 4.8):
        "We initialize alpha to zero for all blocks... leading to u_theta being 
        a linear combination of the first layer embeddings at initialization."
        
        Therefore, at init, Block(x) must equal x (Identity).
        """
        x, U, V = data
        
        # Run forward pass (eval mode to disable dropout if any)
        model.eval()
        with torch.no_grad():
            output = model(x, U, V)
            
        # Check if alpha is initialized to 0
        # Assuming the trainable parameter is named 'alpha'
        alpha_param = None
        for name, param in model.named_parameters():
            if 'alpha' in name:
                alpha_param = param
                break
        
        assert alpha_param is not None, "Could not find 'alpha' parameter in model"
        assert torch.isclose(alpha_param, torch.tensor(0.0)), "Alpha must be initialized to 0"

        # Check identity mapping behavior
        # Tolerance slightly loose for float precision, but should be very close
        assert torch.allclose(output, x, atol=1e-6), \
            "PirateNet Block must be an identity map at initialization (alpha=0)"

    def test_gradients_exist(self, model, data):
        """
        Verifies that gradients propagate to weights and specifically the alpha parameter.
        """
        x, U, V = data
        x.requires_grad = True
        
        output = model(x, U, V)
        loss = output.sum()
        loss.backward()

        # Check input gradients
        assert x.grad is not None
        
        # Check weight gradients
        has_grad = False
        alpha_has_grad = False
        
        for name, param in model.named_parameters():
            if param.grad is not None:
                has_grad = True
                if 'alpha' in name:
                    assert param.grad.norm() != 0.0
                    alpha_has_grad = True
        
        assert has_grad, "No gradients flowing to internal weights"
        assert alpha_has_grad, "Gradient did not reach the alpha parameter (Eq 4.6)"

    def test_trainability_overfit(self, input_dim, data):
        """
        Ensures the block can learn a non-identity transformation.
        """
        x, U, V = data
        # Target is a simple transformation of x (not identity)
        target = x * 2.0 + 1.0 
        
        model = PirateNetBlock(units=input_dim, activation=nn.Tanh())
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        loss_start = 0
        loss_end = 0
        
        for i in range(50):
            optimizer.zero_grad()
            output = model(x, U, V)
            loss = nn.MSELoss()(output, target)
            loss.backward()
            optimizer.step()
            
            if i == 0:
                loss_start = loss.item()
            loss_end = loss.item()

        assert loss_end < loss_start, "Loss failed to decrease on simple overfit task"
        
        # Alpha should diverge from 0 as it learns nonlinearity
        for name, param in model.named_parameters():
            if 'alpha' in name:
                assert not torch.isclose(param, torch.tensor(0.0)), \
                    "Alpha remained 0; model failed to learn nonlinearity"
