import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.graph.sgr import SGRLayer

class TestSGRLayer:
    """
    Test suite for SGRLayer
    Paper: Liang et al., 'Symbolic Graph Reasoning for Semantic Segmentation', NeurIPS 2018.
    """

        
    @pytest.fixture
    def layer_params(self):
        return {
            'in_channels': 64,  # D^l
            'num_nodes': 20,    # M
            'node_dim': 32,     # D^c
            'vocab_dim': 50,    # K
        }

    @pytest.fixture
    def graph_inputs(self, layer_params):
        M = layer_params['num_nodes']
        K = layer_params['vocab_dim']
        # Adjacency matrix (A)
        adj = torch.rand((M, M))
        # Linguistic word embeddings (S) - Eq 3
        word_embs = torch.randn((M, K))
        return adj, word_embs

    @pytest.fixture
    def input_tensor(self, layer_params):
        # Shape: (Batch, Channels, Height, Width)
        return torch.randn(2, layer_params['in_channels'], 16, 16)

    @pytest.fixture
    def model(self, layer_params, graph_inputs):
        adj, word_embs = graph_inputs
        return SGRLayer(
            in_channels=layer_params['in_channels'],
            num_nodes=layer_params['num_nodes'],
            node_feature_dim=layer_params['node_dim'], # Fixed parameter name here
            adj_matrix=adj,
            word_embeddings=word_embs
        )

    # --- Tests ---

    def test_instantiation_and_shape(self, model, input_tensor):
        """
        Verifies the layer initializes and output preserves spatial/channel dims
        (due to Residual Connection in Eq 6).
        """
        output = model(input_tensor)
        
        # Input: (B, C, H, W) -> Output: (B, C, H, W)
        assert output.shape == input_tensor.shape
        assert output.dtype == input_tensor.dtype

    def test_numerical_stability(self, model, input_tensor):
        """
        Checks for NaNs/Infs. Critical because SGR uses two Softmax operations:
        1. Local-to-Semantic Voting (Eq 2)
        2. Semantic-to-Local Mapping (Eq 5)
        """
        output = model(input_tensor)
        assert not torch.isnan(output).any(), "Output contains NaNs"
        assert not torch.isinf(output).any(), "Output contains Infs"

    def test_gradient_flow(self, model, input_tensor):
        """
        Ensures gradients propagate back to trainable weights (W_ps, W_g, W_s, etc.).
        """
        input_tensor.requires_grad = True
        output = model(input_tensor)
        loss = output.mean()
        loss.backward()

        # Check input gradients
        assert input_tensor.grad is not None
        
        # Check weight gradients
        has_grad = False
        for name, param in model.named_parameters():
            if param.grad is not None and param.grad.abs().sum() > 0:
                has_grad = True
                
        assert has_grad, "No gradients flowed to internal parameters"

    def test_overfit_single_batch(self, model, input_tensor):
        """
        Basic sanity check: Can the layer learn to minimize loss on a single batch?
        """
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        target = torch.randn_like(input_tensor)
        
        initial_loss = nn.MSELoss()(model(input_tensor), target).item()
        
        for _ in range(10):
            optimizer.zero_grad()
            output = model(input_tensor)
            loss = nn.MSELoss()(output, target)
            loss.backward()
            optimizer.step()
            
        final_loss = loss.item()
        assert final_loss < initial_loss, "Model failed to reduce loss on a single batch"

    def test_batch_independence(self, model):
        """
        Invariant: Reasoning for Image A should not be affected by Image B in the batch.
        Voting (Eq 2) and Mapping (Eq 5) are sample-specific.
        """
        input_a = torch.randn(1, 64, 16, 16)
        input_b = torch.randn(1, 64, 16, 16)
        
        # Forward pass separately
        out_a = model(input_a)
        out_b = model(input_b)
        
        # Forward pass batched
        batch_in = torch.cat([input_a, input_b], dim=0)
        batch_out = model(batch_in)
        
        # Check equality
        assert torch.allclose(batch_out[0], out_a[0], atol=1e-5)
        assert torch.allclose(batch_out[1], out_b[0], atol=1e-5)
