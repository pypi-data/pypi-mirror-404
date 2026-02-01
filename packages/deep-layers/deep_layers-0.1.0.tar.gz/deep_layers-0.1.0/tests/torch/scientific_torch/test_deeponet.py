import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from deep_layers.torch.scientific.deeponet import DeepONetLayer

class TestDeepONetLayer:
    @pytest.fixture
    def input_dims(self):  # Added self
        return {'m': 50, 'd': 2, 'p': 20, 'batch': 32}

    @pytest.fixture
    def model(self, input_dims):  # Added self
        # Implementation expects lists of features
        return DeepONetLayer(
            branch_features=[input_dims['m'], 64, input_dims['p']], 
            trunk_features=[input_dims['d'], 64, input_dims['p']]
        )

    def test_instantiation_and_shapes(self, model, input_dims):  # Added self
        u = torch.randn(input_dims['batch'], input_dims['m'])
        y = torch.randn(input_dims['batch'], input_dims['d'])
        output = model(u, y)
        assert output.shape == (input_dims['batch'], 1)

    def test_architecture_invariant_dimension_mismatch(self, input_dims):  # Added self
        m, d, p = input_dims['m'], input_dims['d'], input_dims['p']
        with pytest.raises(ValueError):
            # Mismatching the last element (p)
            DeepONetLayer(branch_features=[m, p], trunk_features=[d, p + 5])

    def test_forward_numerical_stability(self, model, input_dims):  # Added self
        u = torch.randn(input_dims['batch'], input_dims['m'])
        y = torch.randn(input_dims['batch'], input_dims['d'])
        output = model(u, y)
        assert torch.isfinite(output).all()

    def test_backward_pass_gradients(self, model, input_dims):  # Added self
        u = torch.randn(input_dims['batch'], input_dims['m'], requires_grad=True)
        y = torch.randn(input_dims['batch'], input_dims['d'], requires_grad=True)
        output = model(u, y)
        output.sum().backward()
        assert any(p.grad is not None for p in model.branch_net.parameters())
        assert any(p.grad is not None for p in model.trunk_net.parameters())

    def test_overfit_simple_operator(self, model, input_dims):  # Added self
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        u = torch.randn(input_dims['batch'], input_dims['m'])
        y = torch.randn(input_dims['batch'], input_dims['d'])
        target = torch.zeros(input_dims['batch'], 1)
        
        for _ in range(10):
            optimizer.zero_grad()
            loss = nn.MSELoss()(model(u, y), target)
            loss.backward()
            optimizer.step()
        assert loss < 1.0

    def test_batch_independence(self, model, input_dims):  # Added self
        model.eval()
        u = torch.randn(2, input_dims['m'])
        y = torch.randn(2, input_dims['d'])
        out_batch = model(u, y)
        out_single = model(u[0:1], y[0:1])
        assert torch.allclose(out_batch[0], out_single[0], atol=1e-5)
