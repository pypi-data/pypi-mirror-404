import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf
from deep_layers.torch.sequence.retention import RetentionLayer

class TestRetentionLayer:
    """
    Test suite for RetentionLayer
    Paper: Sun et al., 'Retentive Network: A Successor to Transformer for Large Language Models', ICLR 2024.
    """

    BATCH_SIZE = 2
    SEQ_LEN = 8
    D_MODEL = 64
    N_HEADS = 4  # Head dim = 16

    @pytest.fixture
    def model(self):
        # Setup based on Section 2.2
        return RetentionLayer(embed_dim=self.D_MODEL, num_heads=self.N_HEADS)

    @pytest.fixture
    def input_tensor(self):
        return torch.randn(self.BATCH_SIZE, self.SEQ_LEN, self.D_MODEL)

    def test_instantiation_and_shape(self, model, input_tensor):
        """Verifies output shape matches (B, L, D) - Eq 9."""
        output = model(input_tensor) 
        assert output.shape == (self.BATCH_SIZE, self.SEQ_LEN, self.D_MODEL)

    def test_numerical_stability(self, model, input_tensor):
        """
        Checks for NaNs/Infs. 
        Crucial for RetNet due to the exponential decay factors (gamma^n) 
        and GroupNorm described in Section 2.2.
        """
        output = model(input_tensor)
        assert not torch.isnan(output).any(), "Output contains NaNs"
        assert not torch.isinf(output).any(), "Output contains Infs"

    def test_parallel_vs_recurrent_equivalence(self, model, input_tensor):
        """
        Paper Section 2.1 & Figure 3: 'Dual form of RetNet'.
        The parallel computation (training) must equal the recurrent computation (inference).
        """
        model.eval()
        
        # 1. Parallel Forward
        with torch.no_grad():
            y_parallel = model(input_tensor)
        
        # 2. Recurrent Forward (step-by-step)
        y_recurrent = []
        state = None 
        
        with torch.no_grad():
            for t in range(self.SEQ_LEN):
                # Slice input to simulate streaming (B, 1, D)
                x_t = input_tensor[:, t:t+1, :]
                out_t, state = model.forward_recurrent(x_t, prev_state=state, seq_idx=t)
                y_recurrent.append(out_t)
                
        y_recurrent = torch.cat(y_recurrent, dim=1)
        
        # Check equivalence
        # Relax tolerance slightly due to float accumulation differences (Parallel sum vs Serial sum)
        assert torch.allclose(y_parallel, y_recurrent, atol=1e-4, rtol=1e-4), \
            "Parallel and Recurrent implementations diverge."

    def test_causality_invariant(self, model):
        """
        Verifies the causal masking property implicit in Retention Eq 5.
        Changing the last token of input should NOT affect the output of the first token.
        """
        x1 = torch.randn(self.BATCH_SIZE, self.SEQ_LEN, self.D_MODEL)
        x2 = x1.clone()
        x2[:, -1, :] = torch.randn(self.BATCH_SIZE, self.D_MODEL) # Change last token

        y1 = model(x1)
        y2 = model(x2)

        # The output for the first token (index 0) must be identical
        assert torch.allclose(y1[:, 0, :], y2[:, 0, :]), "Causal mask failed; future leakage detected."
        # The output for the last token must be different
        assert not torch.allclose(y1[:, -1, :], y2[:, -1, :])

    def test_gradient_propagation(self, model, input_tensor):
        """Standard check that gradients flow through the Swish gate and Retention."""
        output = model(input_tensor)
        loss = output.sum()
        loss.backward()
        
        # Check W_Q, W_K, W_V, W_G (Gate), W_O
        # Accessing parameters generically via named_parameters
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Gradient missing for {name}"
                assert not torch.isnan(param.grad).any(), f"NaN gradient in {name}"

    def test_overfit_small_batch(self, model):
        """Verifies the layer can learn (convergence check)."""
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        x = torch.randn(4, 8, self.D_MODEL)
        target = torch.randn(4, 8, self.D_MODEL)
        
        initial_loss = torch.nn.functional.mse_loss(model(x), target)
        
        for _ in range(10):
            optimizer.zero_grad()
            output = model(x)
            loss = torch.nn.functional.mse_loss(output, target)
            loss.backward()
            optimizer.step()
            
        assert loss < initial_loss, "Model failed to reduce loss on synthetic batch"
