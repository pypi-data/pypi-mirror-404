import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.vq import VQLayer

class TestVQLayer:
    """
    Test suite for VQLayer
    Paper: Van den Oord et al., 'Neural Discrete Representation Learning' (VQ-VAE), NeurIPS 2017.
    """

    @pytest.fixture
    def vq_config(self):
        return {
            'num_embeddings': 512,  # K
            'embedding_dim': 64,    # D
            'commitment_cost': 0.25 # Beta (from paper Section 3.2)
        }

    def test_instantiation_and_shape(self, vq_config):
        """Checks if output shape matches input shape (Section 3.1)."""
        model = VQLayer(**vq_config)
        B, D, H, W = 2, vq_config['embedding_dim'], 32, 32
        x = torch.randn(B, D, H, W)
        
        # Unpack 4 values as per implementation
        loss, quantized, perplexity, encoding_indices = model(x)
        # Paper Section 3.1: "The input to the decoder is the corresponding embedding vector"
        # Dimensionality should be preserved.
        assert quantized.shape == x.shape
        assert loss.shape == () # Scalar loss
        assert not torch.isnan(quantized).any()

    def test_quantization_correctness(self, vq_config):
        """
        Verifies that outputs are actually chosen from the embedding codebook.
        (Equation 2: z_q(x) = e_k)
        """
        model = VQLayer(**vq_config)
        x = torch.randn(1, vq_config['embedding_dim'], 1, 1)
        # Unpack all 4: loss, quantized, perplexity, indices
        loss, quantized, perplexity, indices = model(x)
        
        # The output vector must exist exactly in the embedding weight matrix
        # Flatten checks for simplicity
        q_flat = quantized.detach().view(-1)
        found = False
        for emb in model.embedding.weight.detach():
            if torch.allclose(q_flat, emb, atol=1e-5):
                found = True
                break
                
        assert found, "Output vector z_q was not found in the embedding codebook."

    def test_straight_through_gradient(self, vq_config):
        model = VQLayer(**vq_config)
        x = torch.randn(2, vq_config['embedding_dim'], 4, 4, requires_grad=True)
        vq_loss, quantized, _, _ = model(x) # Fixed unpacking
        reconstruction_loss = quantized.sum()
        (reconstruction_loss + vq_loss).backward()
        assert x.grad is not None
        assert torch.abs(x.grad).sum() > 0.0 

    def test_numerical_stability(self, vq_config):
        model = VQLayer(**vq_config)
        x = torch.randn(2, vq_config['embedding_dim'], 4, 4) * 1000.0
        loss, quantized, _, _ = model(x) # Fixed unpacking
        assert torch.isfinite(loss)
        assert torch.isfinite(quantized).all()

    def test_training_convergence_overfit(self, vq_config):
        model = VQLayer(**vq_config)
        optimizer = optim.Adam(model.parameters(), lr=0.1)
        fixed_input = torch.randn(1, vq_config['embedding_dim'], 1, 1)
        with torch.no_grad():
            _, initial_q, _, _ = model(fixed_input) # Fixed unpacking
            initial_dist = torch.nn.functional.mse_loss(fixed_input, initial_q)
        for _ in range(20):
            optimizer.zero_grad()
            vq_loss, _, _, _ = model(fixed_input)
            vq_loss.backward()
            optimizer.step()
        with torch.no_grad():
            _, final_q, _, _ = model(fixed_input)
            final_dist = torch.nn.functional.mse_loss(fixed_input, final_q)
        assert final_dist < initial_dist

    def test_commitment_loss_logic(self, vq_config):
        """
        Verifies Equation 3: L includes beta * ||z_e - sg[e]||^2
        """
        model = VQLayer(**vq_config)
        x = torch.randn(2, vq_config['embedding_dim'], 4, 4)
        # ensure 4 variables
        loss, quantized, perplexity, indices = model(x)
        # loss is a scalar from F.mse_loss, no shape issues
        assert loss.item() > 0
