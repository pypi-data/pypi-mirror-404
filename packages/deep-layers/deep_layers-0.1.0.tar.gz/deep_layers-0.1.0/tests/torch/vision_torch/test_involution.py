import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.vision.involution import Involution

class TestInvolution:
    """
    Test suite for Involution
    Paper: Li et al., 'Involution: Inverting the Inherence of Convolution for Visual Recognition', CVPR 2021.
    """

    # Test configurations: (Channels, Kernel, Stride, Reduction, Groups)
    TEST_CONFIGS = [
        (16, 3, 1, 2, 1),   # Standard use case
        (32, 7, 2, 4, 16),  # Large kernel, stride, groups
        (3, 3, 1, 1, 1),    # Low channel count (RGB input scenario)
    ]

    @pytest.mark.parametrize("C, K, S, r, G", TEST_CONFIGS)
    def test_instantiation_and_shape(self, C, K, S, r, G):
        """
        Verifies the layer initializes and produces correct output spatial dimensions
        based on standard convolution arithmetic.
        """
        layer = Involution(channels=C, kernel_size=K, stride=S, reduction_ratio=r, group_channels=G)
        
        H, W = 64, 64
        x = torch.randn(2, C, H, W) # NCHW
        out = layer(x)
        
        # Expected output dim: floor((H + 2*padding - K)/S) + 1
        # Assuming "same" padding logic is handled inside or padding=K//2
        expected_h = (H + 2 * (K // 2) - K) // S + 1
        expected_w = (W + 2 * (K // 2) - K) // S + 1
        
        assert out.shape == (2, C, expected_h, expected_w)

    def test_numerical_stability(self):
        """
        Ensures no NaNs or Infs are generated, even with random inputs.
        """
        layer = Involution(channels=16, kernel_size=3, stride=1)
        x = torch.randn(4, 16, 32, 32)
        out = layer(x)
        
        assert not torch.isnan(out).any(), "Output contains NaNs"
        assert not torch.isinf(out).any(), "Output contains Infs"

    def test_gradient_propagation(self):
        """
        Verifies that gradients flow back to both the input and the internal 
        kernel generation weights (W0, W1 in Eq. 6).
        """
        C = 8
        # Ensure group_channels divides C. Default is 16, which is > C.
        # Setting group_channels=4 results in groups=2.
        layer = Involution(channels=C, kernel_size=3, stride=1, group_channels=4)
        x = torch.randn(2, C, 16, 16, requires_grad=True)
        
        out = layer(x)
        loss = out.mean()
        loss.backward()
        
        # 1. Check input gradients
        assert x.grad is not None
        assert torch.abs(x.grad).sum() > 0
        
        # 2. Check layer weight gradients (kernel generation branch)
        # The layer should have trainable parameters for the bottleneck
        has_grads = any(p.grad is not None and torch.abs(p.grad).sum() > 0 
                        for p in layer.parameters())
        assert has_grads, "Gradients did not propagate to layer parameters"

    def test_overfit_small_batch(self):
        """
        Sanity check: Can the layer learn a simple identity-like mapping?
        """
        # Channels must be divisible by group_channels (default 16).
        # Using C=4 and group_channels=4 ensures groups=1.
        layer = Involution(channels=4, kernel_size=3, stride=1, group_channels=4)
        optimizer = torch.optim.Adam(layer.parameters(), lr=0.01)
        
        x = torch.randn(1, 4, 10, 10)
        target = torch.randn(1, 4, 10, 10)
        
        initial_loss = torch.nn.functional.mse_loss(layer(x), target).item()
        
        for _ in range(50):
            optimizer.zero_grad()
            out = layer(x)
            loss = torch.nn.functional.mse_loss(out, target)
            loss.backward()
            optimizer.step()
            
        final_loss = loss.item()
        assert final_loss < initial_loss, "Model failed to reduce loss on a single batch"

    def test_channel_group_correctness(self):
        """
        Paper Eq 4: Kernel is shared across G groups. 
        If G=1, kernels are shared across all channels (spatial-specific, channel-agnostic).
        """
        C, K, G = 16, 3, 1
        layer = Involution(channels=C, kernel_size=K, stride=1, group_channels=G)
        x = torch.randn(1, C, 10, 10)
        
        # Hook or inspect internal weights if possible, otherwise functional check
        # Ensuring code runs with G=1 (fully shared) vs G=C (depthwise behavior)
        out = layer(x)
        assert out.shape == (1, C, 10, 10)

        # Test G=C (Depthwise-like behavior regarding kernel generation)
        layer_dw = Involution(channels=C, kernel_size=K, stride=1, group_channels=C)
        out_dw = layer_dw(x)
        assert out_dw.shape == (1, C, 10, 10)
