import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.graph.ntn import NTNLayer

class TestNTNLayer:
    """
    Test suite for NTNLayer
    Paper: Socher et al., 'Reasoning With Neural Tensor Networks for Knowledge Base Completion', NeurIPS 2013.
    """

    # Constants based on paper / standard usage
    BATCH_SIZE = 32
    INPUT_DIM = 100  # 'd' in the paper
    SLICE_DIM = 4    # 'k' in the paper (number of tensor slices)

    @pytest.fixture
    def layer(self):
        # Instantiate the layer for a single relation R
        return NTNLayer(input_dim=self.INPUT_DIM, slice_dim=self.SLICE_DIM)

    @pytest.fixture
    def inputs(self):
        # e1 and e2 vectors
        e1 = torch.randn(self.BATCH_SIZE, self.INPUT_DIM, requires_grad=True)
        e2 = torch.randn(self.BATCH_SIZE, self.INPUT_DIM, requires_grad=True)
        return e1, e2

    def test_instantiation_and_shapes(self, layer, inputs):
        """
        Verifies the layer outputs a scalar score (batch, 1) as per 
        Equation 1: g(e1, R, e2).
        """
        e1, e2 = inputs
        output = layer(e1, e2)
        
        assert output.dim() == 2, "Output should be 2D (batch, 1)"
        assert output.shape == (self.BATCH_SIZE, 1), f"Expected shape ({self.BATCH_SIZE}, 1), got {output.shape}"

    def test_numerical_stability(self, layer, inputs):
        """
        Ensures forward pass does not generate NaN or Inf.
        """
        e1, e2 = inputs
        output = layer(e1, e2)
        
        assert torch.isfinite(output).all(), "Output contains NaNs or Infs"

    def test_gradients_exist(self, layer, inputs):
        """
        Verifies that gradients propagate back to inputs and internal parameters
        (W, V, b, u).
        """
        e1, e2 = inputs
        output = layer(e1, e2)
        loss = output.mean()
        loss.backward()

        # Check input gradients
        assert e1.grad is not None and torch.norm(e1.grad) > 0, "Gradient did not flow to e1"
        assert e2.grad is not None and torch.norm(e2.grad) > 0, "Gradient did not flow to e2"

        # Check weight gradients
        has_grad_param = False
        for name, param in layer.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} has no gradient"
                has_grad_param = True
        
        assert has_grad_param, "No trainable parameters found in layer"

    def test_overfit_small_batch(self, layer):
        """
        Practical sanity check: Can the layer learn to output 1.0 for a fixed pair?
        """
        optimizer = optim.Adam(layer.parameters(), lr=0.01)
        
        # Fixed inputs
        e1 = torch.randn(4, self.INPUT_DIM)
        e2 = torch.randn(4, self.INPUT_DIM)
        target = torch.ones(4, 1)

        initial_loss = None
        for i in range(100):
            optimizer.zero_grad()
            output = layer(e1, e2)
            loss = nn.MSELoss()(output, target)
            loss.backward()
            optimizer.step()
            
            if i == 0:
                initial_loss = loss.item()

        final_loss = loss.item()
        assert final_loss < initial_loss, "Model failed to reduce loss on trivial task"
        assert final_loss < 0.1, f"Model failed to overfit. Final loss: {final_loss}"

    def test_paper_invariant_non_commutative(self, layer):
        """
        Paper Section 3.1 implies the Tensor W is not necessarily symmetric.
        Therefore g(e1, e2) != g(e2, e1) generally.
        """
        e1 = torch.randn(self.BATCH_SIZE, self.INPUT_DIM)
        e2 = torch.randn(self.BATCH_SIZE, self.INPUT_DIM)
        
        out_12 = layer(e1, e2)
        out_21 = layer(e2, e1)
        
        # Assert that the outputs are sufficiently different
        diff = (out_12 - out_21).abs().sum()
        assert diff > 1e-4, "NTN output appears commutative (symmetric), which limits expressiveness."
