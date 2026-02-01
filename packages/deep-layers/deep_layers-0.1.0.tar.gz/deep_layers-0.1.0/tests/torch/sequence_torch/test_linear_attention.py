import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.sequence.linear_attention import LinearAttentionLayer

class TestLinearAttentionLayer:
    """
    Test suite for LinearAttentionLayer
    Paper: Katharopoulos et al., 'Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention', ICML 2020.
    """

    @pytest.fixture
    def layer_config(self):
        return {'dim': 64, 'heads': 4}

    def test_instantiation_and_shape(self, layer_config):
        """
        Verifies the layer initializes and produces outputs of the same shape 
        as inputs (Eq. 2 & 6).
        """
        layer = LinearAttentionLayer(dim=layer_config['dim'], heads=layer_config['heads'])
        B, N, D = 2, 128, 64
        x = torch.randn(B, N, D)
        
        # Implementation forward(x) projects internally to Q,K,V
        output = layer(x)
        assert output.shape == (B, N, D), f"Expected {(B, N, D)}, got {output.shape}"

    def test_numerical_stability(self):
        """
        The feature map phi(x) = elu(x) + 1 (Eq. 7) is non-negative.
        However, denominator aggregation in Eq. 5/12 could be small.
        This tests robustness against NaNs/Infs with varying input scales.
        """
        layer = LinearAttentionLayer(dim=32)
        
        # Test with standard normal
        x_norm = torch.randn(2, 50, 32)
        out_norm = layer(x_norm)
        assert not torch.isnan(out_norm).any(), "Output contains NaNs with normal input"
        
        # Test with large negative values (stressing the elu+1)
        x_neg = torch.randn(2, 50, 32) - 10.0
        out_neg = layer(x_neg)
        assert not torch.isnan(out_neg).any(), "Output contains NaNs with negative input"

    def test_gradient_flow(self):
        """
        Verifies gradients propagate through the layer.
        """
        B, N, D = 2, 64, 32
        x = torch.randn(B, N, D, requires_grad=True)
        
        layer = LinearAttentionLayer(dim=D)
        output = layer(x)
        
        loss = output.sum()
        loss.backward()
        
        assert x.grad is not None, "Gradient did not flow to input"
        # Check internal projection weights
        assert layer.to_qkv.weight.grad is not None, "Gradient did not flow to weights"

    def test_causal_masking_property(self):
        """
        Paper Section 3.3: 'Transformers are RNNs' relies on causal masking.
        We verify that modifying the LAST token in the input does NOT affect 
        the output of the FIRST token.
        """
        layer = LinearAttentionLayer(dim=32)
        # Note: causal masking in this implementation is controlled by the 'causal' argument
        # We need to manually invoke it, usually LinearAttentionLayer takes 'causal' in forward 
        # but the provided implementation signature is forward(self, x, causal=False, mask=None)
        
        B, N, D = 1, 10, 32
        
        # Create two inputs identical except for the last timestep
        input1 = torch.randn(B, N, D)
        input2 = input1.clone()
        input2[:, -1, :] = torch.randn(1, D) # Change last token
        
        # Enable causal mode
        out1 = layer(input1, causal=True)
        out2 = layer(input2, causal=True)
        
        # Check that output at t=0 is identical (since it can't attend to future)
        # Using a small epsilon for float precision
        assert torch.allclose(out1[:, 0, :], out2[:, 0, :], atol=1e-5), \
            "Causality violated: Future token change affected past output."
        
        # Check that output at t=last IS different
        assert not torch.allclose(out1[:, -1, :], out2[:, -1, :]), \
            "Logic error: Changed input did not affect local output."

    def test_overfit_small_batch(self):
        """
        Basic sanity check: Can the layer actually learn a simple identity mapping?
        """
        B, N, D = 1, 10, 16
        layer = LinearAttentionLayer(dim=D)
        optimizer = optim.Adam(layer.parameters(), lr=1e-3)
        
        target = torch.randn(B, N, D)
        input_data = torch.randn(B, N, D)
        
        losses = []
        for _ in range(50):
            optimizer.zero_grad()
            out = layer(input_data)
            loss = torch.nn.functional.mse_loss(out, target)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        
        assert losses[-1] < losses[0], "Loss did not decrease; layer is not learning."
