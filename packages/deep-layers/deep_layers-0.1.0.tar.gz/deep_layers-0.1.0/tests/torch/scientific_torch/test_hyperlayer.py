import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from deep_layers.torch.scientific.hyperlayer import HyperLayer

class TestHyperLayer:
    @pytest.fixture
    def model_config(self):  # Added self
        return {
            'input_size': 32,
            'hidden_size': 128,
            'hyper_hidden_size': 16
        }

    @pytest.fixture
    def device(self):  # Added self
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def test_instantiation_and_shapes(self, model_config):  # Added self
        batch_size = 8
        model = HyperLayer(**model_config)
        x = torch.randn(batch_size, model_config['input_size'])
        h = torch.zeros(batch_size, model_config['hidden_size'])
        c = torch.zeros(batch_size, model_config['hidden_size'])
        hh = torch.zeros(batch_size, model_config['hyper_hidden_size'])
        hc = torch.zeros(batch_size, model_config['hyper_hidden_size'])
        
        h_next, _ = model(x, ((h, c), (hh, hc)))
        assert h_next.shape == (batch_size, model_config['hidden_size'])

    def test_numerical_stability(self, model_config):  # Added self
        model = HyperLayer(**model_config)
        x = torch.randn(16, model_config['input_size'])
        h = torch.randn(16, model_config['hidden_size'])
        c = torch.randn(16, model_config['hidden_size'])
        hh = torch.randn(16, model_config['hyper_hidden_size'])
        hc = torch.randn(16, model_config['hyper_hidden_size'])
        
        h_out, _ = model(x, ((h, c), (hh, hc)))
        assert torch.isfinite(h_out).all()

    def test_gradient_flow_end_to_end(self, model_config):  # Added self
        model = HyperLayer(**model_config)
        x = torch.randn(4, model_config['input_size'], requires_grad=True)
        h = torch.zeros(4, model_config['hidden_size'])
        c = torch.zeros(4, model_config['hidden_size'])
        hh = torch.zeros(4, model_config['hyper_hidden_size'])
        hc = torch.zeros(4, model_config['hyper_hidden_size'])
        
        h_out, _ = model(x, ((h, c), (hh, hc)))
        h_out.mean().backward()
        
        for param in model.parameters():
            assert param.grad is not None

    def test_overfit_small_batch(self, model_config, device):  # Added self
        model = HyperLayer(**model_config).to(device)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        x = torch.randn(10, model_config['input_size']).to(device)
        target = torch.ones(10, model_config['hidden_size']).to(device)
        h = torch.zeros(10, model_config['hidden_size']).to(device)
        c = torch.zeros(10, model_config['hidden_size']).to(device)
        hh = torch.zeros(10, model_config['hyper_hidden_size']).to(device)
        hc = torch.zeros(10, model_config['hyper_hidden_size']).to(device)

        for _ in range(5):
            optimizer.zero_grad()
            h_out, _ = model(x, ((h, c), (hh, hc)))
            loss = nn.MSELoss()(h_out, target)
            loss.backward()
            optimizer.step()
        assert loss < 2.0

    def test_dynamic_weight_determinism(self, model_config):  # Added self
        model = HyperLayer(**model_config)
        model.eval()
        x = torch.randn(2, model_config['input_size'])
        h = torch.randn(2, model_config['hidden_size'])
        c = torch.randn(2, model_config['hidden_size'])
        hh = torch.randn(2, model_config['hyper_hidden_size'])
        hc = torch.randn(2, model_config['hyper_hidden_size'])
        
        with torch.no_grad():
            out1, _ = model(x, ((h, c), (hh, hc)))
            out2, _ = model(x, ((h, c), (hh, hc)))
        assert torch.allclose(out1, out2)
