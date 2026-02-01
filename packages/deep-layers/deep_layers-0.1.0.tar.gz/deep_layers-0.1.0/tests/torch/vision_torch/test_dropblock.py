import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.vision.dropblock import DropBlock

class TestDropBlock:
    """
    Test suite for DropBlock
    Paper: Ghiasi et al., 'DropBlock: A regularization method for convolutional networks', NeurIPS 2018.
    """

    @pytest.fixture
    def layer_cls(self):
        return DropBlock

    def test_instantiation_and_shape(self, layer_cls):
        """Test output shape matches input shape (NCHW)."""
        block_size = 3
        drop_prob = 0.2 # Equivalent to keep_prob = 0.8
        
        # Standard PyTorch Input: (Batch, Channels, Height, Width)
        input_shape = (4, 16, 32, 32)
        inputs = torch.randn(input_shape)
        
        layer = layer_cls(block_size=block_size, drop_prob=drop_prob)
        layer.train() # Force training mode
        
        outputs = layer(inputs)
        assert outputs.shape == input_shape

    def test_eval_mode_identity(self, layer_cls):
        """
        Paper Section 3: Eval/Inference mode returns input A.
        """
        layer = layer_cls(block_size=5, drop_prob=0.5)
        layer.eval() # Set to evaluation mode
        
        inputs = torch.randn(2, 3, 16, 16)
        outputs = layer(inputs)
        
        assert torch.allclose(inputs, outputs), "Eval mode must be identity"

    def test_training_mode_drops_values(self, layer_cls):
        """Test that values are zeroed out in training mode."""
        layer = layer_cls(block_size=3, drop_prob=0.5)
        layer.train()
        
        inputs = torch.rand(2, 3, 20, 20) + 1.0 # Ensure no natural zeros
        outputs = layer(inputs)
        
        assert not torch.allclose(inputs, outputs)
        assert (outputs == 0).any(), "Some elements should be zeroed out"

    def test_variable_input_size(self, layer_cls):
        """
        Paper Eq 1: gamma depends on feat_size.
        Implementation must handle dynamic H/W dimensions.
        """
        layer = layer_cls(block_size=3, drop_prob=0.2)
        layer.train()
        
        out1 = layer(torch.randn(1, 1, 20, 20))
        out2 = layer(torch.randn(1, 1, 40, 40)) # Different spatial dims
        
        assert out1.shape == (1, 1, 20, 20)
        assert out2.shape == (1, 1, 40, 40)

    def test_gradients_exist(self, layer_cls):
        """Check backward pass."""
        layer = layer_cls(block_size=3, drop_prob=0.4) # keep_prob 0.6
        layer.train()
        
        inputs = torch.randn(2, 4, 16, 16, requires_grad=True)
        outputs = layer(inputs)
        
        loss = outputs.sum()
        loss.backward()
        
        assert inputs.grad is not None
        assert torch.abs(inputs.grad).sum() > 0

    def test_edge_case_keep_all(self, layer_cls):
        """If drop_prob is 0.0, nothing should be dropped even in train mode."""
        layer = layer_cls(block_size=3, drop_prob=0.0)
        layer.train()
        
        inputs = torch.randn(2, 3, 10, 10)
        outputs = layer(inputs)
        
        assert torch.allclose(inputs, outputs), "drop_prob=0.0 should not drop anything"

    def test_normalization_statistic(self, layer_cls):
        """
        Verify mean preservation (Paper Section 3 normalization).
        The expected value of the output should match input.
        """
        torch.manual_seed(42)
        # Large batch/dim for stability
        inputs = torch.ones(20, 1, 60, 60)
        
        layer = layer_cls(block_size=5, drop_prob=0.3)
        layer.train()
        
        outputs = layer(inputs)
        
        input_mean = inputs.mean().item()
        output_mean = outputs.mean().item()
        
        # Check within 10% tolerance
        assert abs(input_mean - output_mean) / input_mean < 0.1

    def test_simple_optimization(self, layer_cls):
        """Sanity check: can we overfit a tiny batch through this layer?"""
        torch.manual_seed(42)
        layer = layer_cls(block_size=2, drop_prob=0.2)
        layer.train()
        
        # Simple task: learn to output zeros
        param = torch.nn.Parameter(torch.randn(1, 1, 10, 10))
        opt = torch.optim.SGD([param], lr=0.1)
        
        # Measure parameter magnitude directly (L1 norm)
        # The output loss is noisy due to random masking, so comparing 
        # initial vs final loss is unreliable. Checking if parameters shrink 
        # is a robust verification of gradient flow.
        initial_param_norm = param.abs().mean().item()
        
        for i in range(20):
            opt.zero_grad()
            out = layer(param) # Noise injected here
            loss = out.abs().mean()
            loss.backward()
            opt.step()
            
        final_param_norm = param.abs().mean().item()
        
        assert final_param_norm < initial_param_norm
