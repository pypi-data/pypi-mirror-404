import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.sequence.hyena import HyenaOperator

class TestHyenaOperator:
    """
    Test suite for HyenaOperator
    Paper: Poli et al., 'Hyena Hierarchy: Towards Larger Convolutional Language Models', ICML 2023.
    """

    @pytest.fixture
    def hyena_config(self):
        return {
            "d_model": 64,
            "l_max": 128,
            "order": 2,  # Standard Hyena order mentioned in experiments
            "filter_order": 64
        }

    @pytest.fixture
    def model(self, hyena_config):
        return HyenaOperator(**hyena_config)

    def test_instantiation_and_shape(self, model, hyena_config):
        """
        Verifies the layer preserves the sequence length and embedding dimension.
        Hyena is a drop-in replacement for Attention (B, L, D) -> (B, L, D).
        """
        B, L, D = 4, hyena_config['l_max'], hyena_config['d_model']
        x = torch.randn(B, L, D)
        
        output = model(x)
        
        assert output.shape == (B, L, D)
        assert not torch.isnan(output).any()

    @pytest.mark.parametrize("seq_len", [32, 128, 131]) # Check power of 2 and odd lengths (FFT edge cases)
    def test_variable_sequence_lengths(self, hyena_config, seq_len):
        """
        Hyena uses global convolutions via FFT. This checks if the layer 
        handles sequence lengths up to l_max, including non-power-of-2s.
        """
        # The implementation dynamically generates filters based on input length L.
        # So we can test lengths > l_max without issues.
            
        model = HyenaOperator(**hyena_config)
        B, D = 2, hyena_config['d_model']
        x = torch.randn(B, seq_len, D)
        
        output = model(x)
        assert output.shape == (B, seq_len, D)

    def test_causality_invariant(self, model, hyena_config):
        """
        CRITICAL: Hyena is designed for autoregressive tasks. 
        Changing input at t=k should NOT affect output at t < k.
        This ensures the 'Shift' and 'Toeplitz' matrices are lower triangular.
        """
        model.eval() # Ensure dropout doesn't interfere
        B, L, D = 2, hyena_config['l_max'], hyena_config['d_model']
        
        x = torch.randn(B, L, D)
        
        # Create a copy and modify only the LAST token
        x_mod = x.clone()
        x_mod[:, -1, :] = torch.randn(B, D)
        
        with torch.no_grad():
            y1 = model(x)
            y2 = model(x_mod)
        
        # Outputs should be identical up to the last position.
        # Note: FFT convolution in float32 can have global numerical noise 
        # relative to the magnitude of the signal. 
        # With outputs ~200, rtol=1e-4 allows error ~0.02, which covers 8e-5.
        assert torch.allclose(y1[:, :-1, :], y2[:, :-1, :], rtol=1e-4, atol=1e-4), \
            "Causality violation: Future token modified past output."
        
        # Last position should ideally be different
        assert not torch.allclose(y1[:, -1, :], y2[:, -1, :]), \
            "Output at modified position did not change."

    def test_numerical_stability_and_gradients(self, model, hyena_config):
        """
        Checks for NaN propagation during backward pass, common in FFT-based 
        convolutions or exponential activation functions.
        """
        B, L, D = 4, hyena_config['l_max'], hyena_config['d_model']
        x = torch.randn(B, L, D, requires_grad=True)
        
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        # Check inputs gradient
        assert x.grad is not None
        assert not torch.isnan(x.grad).any()
        assert not torch.isinf(x.grad).any()
        
        # Check weights gradient
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"
                assert not torch.isnan(param.grad).any(), f"NaN in grad for {name}"

    def test_overfit_small_batch(self, model, hyena_config):
        """
        Practical sanity check: Can the layer learn an identity mapping 
        or simple transformation on a small batch?
        """
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()
        
        B, L, D = 2, 32, hyena_config['d_model']
        x = torch.randn(B, L, D)
        target = torch.randn(B, L, D) # Random target to memorize
        
        for _ in range(50):
            optimizer.zero_grad()
            output = model(x)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
        
        # Loss should decrease significantly
        assert loss.item() < 1.0, f"Model failed to converge on trivial task. Final loss: {loss.item()}"
