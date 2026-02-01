import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.coral import CORALLayer

class TestCORALLayer:
    """
    Test suite for CORALLayer
    Paper: Serrano et al., 'Operator Learning with Neural Fields', NeurIPS 2023.
    """

    @pytest.fixture
    def model_config(self):
        return {
            'in_features': 2,
            'out_features': 1,
            "latent_dim": 1,
            'w0': 30.0
        }

    def test_instantiation(self, model_config):
        from deep_layers.torch.scientific.coral import CORALLayer
        model = CORALLayer(**model_config)
        assert isinstance(model, nn.Module)

    def test_forward_shape(self, model_config):
        """
        Test generic shape consistency.
        Input: Coords (B, N, in_dim), Latent (B, latent_dim)
        Output: (B, N, out_dim)
        """
        B, N = 4, 100
        model = CORALLayer(**model_config)
        coords = torch.randn(B, N, model_config['in_features']) # Correct key
        latents = torch.randn(B, model_config['out_features']) # Use out_features for modulation size
        output = model(coords, latents)
        
        assert output.shape == (B, N, model_config['out_features'])
        assert not torch.isnan(output).any()

    def test_coordinate_independence(self, model_config):
        """
        Paper Invariant: CORAL works on 'General Geometries' and irregular grids.
        The model should accept different numbers of query points (N) in the forward pass.
        """
        model = CORALLayer(**model_config)
        B = 2
        latent = torch.randn(B, model_config['latent_dim'])

        # Grid 1: 50 points
        coords_1 = torch.randn(B, 50, model_config['in_features'])
        out_1 = model(coords_1, latent)
        assert out_1.shape == (B, 50, model_config['out_features'])

        # Grid 2: 200 points (same model, same latent)
        coords_2 = torch.randn(B, 200, model_config['in_features'])
        out_2 = model(coords_2, latent)
        assert out_2.shape == (B, 200, model_config['out_features'])

    def test_latent_modulation_effect(self, model_config):
        model = CORALLayer(**model_config)
        B, N = 1, 10
        coords = torch.randn(B, N, model_config['in_features'])
        
        z1 = torch.randn(B, model_config['latent_dim'])
        z2 = torch.randn(B, model_config['latent_dim'])
        
        out1 = model(coords, z1)
        out2 = model(coords, z2)
        
        # Outputs should be significantly different
        assert not torch.allclose(out1, out2, atol=1e-5)

    def test_gradient_flow(self, model_config):
        """Test if gradients propagate to both weights and latent codes."""
        model = CORALLayer(**model_config)
        B, N = 2, 50
        coords = torch.randn(B, N, model_config['in_features'])
        latents = torch.randn(B, model_config['latent_dim'], requires_grad=True)
        
        output = model(coords, latents)
        target = torch.randn_like(output)
        loss = torch.nn.MSELoss()(output, target)
        loss.backward()

        # Check weights gradients
        for param in model.parameters():
            assert param.grad is not None
        
        # Check latent gradients (crucial for the auto-decoding step in CORAL)
        assert latents.grad is not None
        assert torch.norm(latents.grad) > 0

    def test_overfit_single_sample(self, model_config):
        """
        Trainability test: Fit a simple sine wave.
        """
        # Increase width and add readout for robust fitting
        config = model_config.copy()
        config['out_features'] = 32
        
        model = CORALLayer(**config, is_first=True)
        readout = nn.Linear(32, 1)
        
        optimizer = torch.optim.Adam(list(model.parameters()) + list(readout.parameters()), lr=1e-2)
        
        B, N = 1, 200
        coords = torch.rand(B, N, config['in_features']) * 2 - 1
        latents = torch.randn(B, config['latent_dim'])
        target = torch.sin(3.14 * coords[..., 0:1])
        
        for i in range(500):
            optimizer.zero_grad()
            features = model(coords, latents)
            pred = readout(features)
            loss = torch.nn.MSELoss()(pred, target)
            loss.backward()
            optimizer.step()
            
        assert loss.item() < 0.1
