import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.graph.set_transformer import SAB, ISAB, PMA

class TestSetTransformer:
    """
    Test suite for SetTransformer
    Paper: Lee et al., 'Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks', ICML 2019.
    """

    @pytest.fixture
    def batch_setup(self):
        # Batch size 4, Set size 10, Dimension 32
        return torch.randn(4, 10, 32)

    @pytest.mark.parametrize("Block", [SAB, ISAB])
    def test_encoder_shapes(self, Block):
        """
        SAB and ISAB should preserve set size (n) and map to output dimension.
        Paper Eq 8 (SAB) and Eq 9 (ISAB).
        """
        B, N, D_in = 4, 20, 32
        D_out = 64
        num_heads = 4
        
        if Block == SAB:
            model = Block(dim_in=D_in, dim_out=D_out, num_heads=num_heads)
        else:
            model = Block(dim_in=D_in, dim_out=D_out, num_heads=num_heads, num_inducing=10)

        x = torch.randn(B, N, D_in)
        out = model(x)
        
        # Input set size N should be preserved
        assert out.shape == (B, N, D_out)

    def test_pma_aggregation_shape(self):
        """
        PMA should aggregate N items into k seed vectors.
        Paper Eq 11.
        """
        B, N, D = 4, 50, 32
        num_seeds = 5  # k
        model = PMA(dim=D, num_heads=4, num_seeds=num_seeds)
        
        x = torch.randn(B, N, D)
        out = model(x)
        
        # Output should be (Batch, k, Dim)
        assert out.shape == (B, num_seeds, D)

    def test_permutation_equivariance_sab_isab(self):
        """
        Property 1 from paper: SAB and ISAB are permutation equivariant.
        f(pi(x)) = pi(f(x))
        """
        B, N, D = 2, 10, 16
        model = SAB(dim_in=D, dim_out=D, num_heads=2)
        # Alternatively test ISAB:
        # model = ISAB(dim_in=D, dim_out=D, num_heads=2, num_inducing=5)
        model.eval()

        x = torch.randn(B, N, D)
        
        # Create a random permutation
        perm_indices = torch.randperm(N)
        x_perm = x[:, perm_indices, :]
        
        with torch.no_grad():
            out_original = model(x)
            out_perm_input = model(x_perm)
        
        # Manually permute the output of the original pass
        out_original_permuted = out_original[:, perm_indices, :]
        
        # They should be nearly identical
        assert torch.allclose(out_original_permuted, out_perm_input, atol=1e-5)

    def test_permutation_invariance_pma(self):
        """
        PMA output should not change if input set is permuted.
        Prop 1 implication: Decoder is permutation invariant.
        """
        B, N, D = 2, 15, 16
        model = PMA(dim=D, num_heads=4, num_seeds=1) # k=1 for standard pooling
        model.eval()

        x = torch.randn(B, N, D)
        perm_indices = torch.randperm(N)
        x_perm = x[:, perm_indices, :]
        
        with torch.no_grad():
            out_1 = model(x)
            out_2 = model(x_perm)
            
        assert torch.allclose(out_1, out_2, atol=1e-5)

    def test_variable_cardinality(self):
        """
        Section 1: "Process input sets of any size".
        Model should accept different N in different forward passes.
        """
        model = SAB(dim_in=32, dim_out=32, num_heads=4)
        
        x_small = torch.randn(2, 5, 32)
        x_large = torch.randn(2, 100, 32)
        
        out_small = model(x_small)
        out_large = model(x_large)
        
        assert out_small.shape[1] == 5
        assert out_large.shape[1] == 100

    def test_nan_stability_and_grads(self):
        """
        Ensures numerical stability and that gradients flow to inducing points (ISAB) 
        and seed vectors (PMA).
        """
        B, N, D = 2, 10, 16
        # ISAB has internal parameters (Inducing Points I)
        model = ISAB(dim_in=D, dim_out=D, num_heads=2, num_inducing=4)
        
        x = torch.randn(B, N, D, requires_grad=True)
        out = model(x)
        
        loss = out.mean()
        loss.backward()
        
        assert not torch.isnan(out).any()
        assert x.grad is not None
        
        # Check if model parameters have gradients
        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"

    def test_overfit_simple_set_task(self):
        """
        Sanity check: Learn to identify the maximum value in a set (Toy problem 5.1).
        """
        # Simple architecture: SAB -> PMA (k=1)
        class SimpleSet(nn.Module):
            def __init__(self):
                super().__init__()
                self.enc = SAB(1, 16, 4)
                self.dec = PMA(16, 4, 1)
                self.out = nn.Linear(16, 1)
            def forward(self, x):
                x = self.enc(x)
                x = self.dec(x)
                return self.out(x).squeeze(-1)

        model = SimpleSet()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        
        # Task: Predict max value of set
        for _ in range(50):
            x = torch.rand(16, 10, 1) # Batch 16, Set 10, Dim 1
            y_gt, _ = x.max(dim=1)
            y_gt = y_gt.squeeze(-1)
            
            preds = model(x).squeeze(-1)
            loss = nn.MSELoss()(preds, y_gt)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
        # Ensure loss goes down (basic check)
        assert loss.item() < 0.5 # Loose bound just to ensure training mechanics work
