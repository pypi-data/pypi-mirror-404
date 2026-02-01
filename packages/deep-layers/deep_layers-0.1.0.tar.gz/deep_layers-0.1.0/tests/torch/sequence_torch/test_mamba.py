import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf
from deep_layers.torch.sequence.mamba import MambaBlock

class TestMambaBlock:
    """
    Test suite for MambaBlock
    Paper: Gu & Dao, 'Mamba: Linear-Time Sequence Modeling with Selective State Spaces', arXiv:2312.00752.
    """

    @pytest.fixture
    def device(self):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @pytest.fixture
    def d_model(self):
        return 64

    @pytest.fixture
    def model(self, d_model, device):
        """
        Instantiates the Mamba block based on paper defaults:
        D=64, N=16 (state dim), E=2 (expansion), kernel=4.
        """
        block = MambaBlock(
            d_model=d_model,
            d_state=16,
            d_conv=4,
            expand=2
        ).to(device)
        return block

    def test_shape_and_forward(self, model, d_model, device):
        """
        Verifies input (B, L, D) produces output (B, L, D).
        Mamba preserves sequence length and dimension.
        """
        B, L = 2, 128
        x = torch.randn(B, L, d_model, device=device)
        
        y = model(x)
        
        assert y.shape == (B, L, d_model), f"Expected shape {(B, L, d_model)}, got {y.shape}"
        assert torch.isfinite(y).all(), "Output contains NaNs or Infs"

    @pytest.mark.parametrize("seq_len", [32, 1024])
    def test_variable_sequence_length(self, model, d_model, seq_len, device):
        """
        Mamba should handle variable sequence lengths without recompilation 
        or shape mismatches, as it is a sequence model.
        """
        x = torch.randn(1, seq_len, d_model, device=device)
        y = model(x)
        assert y.shape[1] == seq_len

    def test_causality_invariant(self, model, d_model, device):
        """
        CRITICAL PAPER INVARIANT:
        Mamba is causal. The output at time t should NOT depend on inputs at time t+k.
        We test this by changing the last token of the input and asserting 
        that the output for all previous tokens (0 to L-2) remains identical.
        """
        B, L = 2, 20
        x = torch.randn(B, L, d_model, device=device)
        
        # 1. Forward pass original
        with torch.no_grad():
            y1 = model(x)
        
        # 2. Modify only the LAST token in the sequence
        x_mod = x.clone()
        x_mod[:, -1, :] = torch.randn(B, d_model, device=device)
        
        with torch.no_grad():
            y2 = model(x_mod)
        
        # 3. Check that y1 and y2 are identical up to the last token
        # (The last output token usually changes, but previous ones must not)
        diff = (y1[:, :-1, :] - y2[:, :-1, :]).abs().max()
        
        assert diff < 1e-5, f"Causality violation! Past outputs changed when future input changed. Max diff: {diff}"

    def test_backward_gradient_flow(self, model, d_model, device):
        """
        Ensures the selective scan and projections are differentiable.
        """
        B, L = 2, 16
        x = torch.randn(B, L, d_model, device=device, requires_grad=True)
        
        y = model(x)
        loss = y.sum()
        loss.backward()

        # Check input gradients
        assert x.grad is not None, "Input gradient missing"
        assert torch.isfinite(x.grad).all(), "Input gradient has NaNs"
        
        # Check weight gradients (sample a few)
        has_grad = False
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} has no gradient"
                assert torch.isfinite(param.grad).all(), f"Parameter {name} grad has NaNs"
                has_grad = True
                
        assert has_grad, "No parameters received gradients"

    def test_selectivity_overfit(self, device):
        """
        Trainability Sanity Check:
        Can a small Mamba block memorize a simple pattern?
        Since Mamba uses 'Selectivity' to solve the 'Selective Copying' task,
        it should easily overfit a small random target.
        """
        # Small model for speed
        tiny_model = MambaBlock(d_model=32, d_state=16, expand=2).to(device)
        
        optimizer = torch.optim.AdamW(tiny_model.parameters(), lr=1e-3)
        
        # Fixed input and target
        x = torch.randn(4, 16, 32, device=device)
        target = torch.randn(4, 16, 32, device=device)
        
        initial_loss = None
        final_loss = None
        
        for i in range(50): # Few steps should be enough to see a drop
            optimizer.zero_grad()
            y = tiny_model(x)
            loss = torch.nn.functional.mse_loss(y, target)
            loss.backward()
            optimizer.step()
            
            if i == 0:
                initial_loss = loss.item()
            final_loss = loss.item()
            
        assert final_loss < initial_loss, f"Loss did not decrease. Init: {initial_loss}, Final: {final_loss}"
