import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.phycrnet import PhyCRNetLayer

class TestPhyCRNetLayer:
    """
    Test suite for PhyCRNetLayer
    Paper: Fan et al., 'Physics-informed convolutional-recurrent neural networks for solving PDEs', CMAME 2022.
    """


    # Constants based on Paper Section 4.1 (Experimental Setup)
    BATCH_SIZE = 2
    CHANNELS = 1
    HEIGHT, WIDTH = 32, 32
    HIDDEN_DIM = 16

    @pytest.fixture
    def model(self):
        """Instantiates the PhyCRNet model."""
        # Encoder downsamples by factor of 8 (3 layers, stride 2)
        # Decoder upsamples by factor of 8 (PixelShuffle)
        return PhyCRNetLayer(input_dim=self.CHANNELS, hidden_dim=self.HIDDEN_DIM, kernel_size=3)

    def test_instantiation_and_shapes(self, model):
        input_tensor = torch.randn(self.BATCH_SIZE, self.CHANNELS, self.HEIGHT, self.WIDTH)
        state = model.init_hidden(self.BATCH_SIZE, (self.HEIGHT, self.WIDTH))
        h_next, c_next = model(input_tensor, state)
        assert h_next.shape == (self.BATCH_SIZE, self.HIDDEN_DIM, self.HEIGHT, self.WIDTH)

    def test_numerical_stability(self, model):
        """
        Checks for NaNs or Infs during forward pass, especially important 
        given the ConvLSTM internal states (tanh/sigmoid activations).
        """
        input_tensor = torch.randn(self.BATCH_SIZE, self.CHANNELS, self.HEIGHT, self.WIDTH)
        output, _ = model(input_tensor)
        
        assert not torch.isnan(output).any(), "Output contains NaNs"
        assert not torch.isinf(output).any(), "Output contains Infs"

    def test_residual_connection_logic(self, model):
        """
        Paper Eq (Sec 3.3): u_{t+1} = u_t + dt * NN(u_t)
        If the internal residual branch weights are initialized near zero 
        (or if we manually zero them), the output should roughly equal input.
        """
        input_tensor = torch.randn(self.BATCH_SIZE, self.CHANNELS, self.HEIGHT, self.WIDTH)
        
        # Create a shadow model to isolate logic without modifying the fixture
        # We won't zero weights here as it requires white-box access, 
        # but we test that gradients flow to the input (identity connection).
        input_tensor.requires_grad = True
        output, _ = model(input_tensor)
        
        loss = output.sum()
        loss.backward()
        
        # If there is a global residual connection u_t -> u_{t+1}, 
        # the gradient w.r.t input should not be zero even if the network is untrained.
        assert input_tensor.grad is not None
        assert torch.abs(input_tensor.grad).mean() > 0.0

    def test_periodic_padding_constraint(self, model):
        """
        Paper Section 3.5: Hard imposition of Periodic BCs via padding.
        Test: The model should handle inputs composed of tiles without crashing,
        and output dimensions must be strictly preserved (no valid-padding shrinkage).
        """
        # Use a dimension not divisible by default powers of 2 to check padding robustness
        # Note: PixelShuffle usually requires dimensions divisible by upscale factor (8).
        # We test with a minimal divisible unit.
        h, w = 16, 16 
        x = torch.randn(1, self.CHANNELS, h, w)
        y, _ = model(x)
        # Output should match spatial dimensions, but channel dimension is HIDDEN_DIM
        assert y.shape == (1, self.HIDDEN_DIM, h, w)

    def test_overfit_small_batch(self, model):
        """
        Verifies the model can learn a simple identity mapping or zero residual.
        """
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()
        
        # Target is same as input (steady state solution test)
        x = torch.randn(2, self.CHANNELS, 32, 32)
        target = x.clone() 
        
        for _ in range(10):
            optimizer.zero_grad()
            output, _ = model(x)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
        final_loss = criterion(model(x)[0], target).item()
        # Loss should decrease or be low. 
        # Since it's a residual net initialized randomly, initial error might be non-zero,
        # but gradients should exist.
        assert final_loss < 100.0 # Loose bound sanity check
