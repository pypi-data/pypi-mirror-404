import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.scientific.sparse_memory import SparseMemoryLayer

class TestSparseMemoryLayer:
    """
    Test suite for SparseMemoryLayer
    Paper: Rae et al., 'Scaling Memory-Augmented Neural Networks with Sparse Reads and Writes', 2016.
    """
    @pytest.fixture
    def sam_params(self):
        return {
            'input_size': 10,
            'hidden_size': 20,
            'memory_slots': 128,  # N
            'memory_dim': 16,     # M
            'k_sparse': 4     # K
        }

    @pytest.fixture
    def sam_layer(self, sam_params):
        return SparseMemoryLayer(**sam_params)

    def test_instantiation(self, sam_layer):
        """Checks if the layer initializes without errors."""
        assert isinstance(sam_layer, nn.Module)

    def test_forward_shape(self, sam_layer, sam_params):
        batch_size = 8
        x = torch.randn(batch_size, sam_params['input_size'])
        state = sam_layer.initial_state(batch_size, x.device)
        output, next_state = sam_layer(x, state)
        assert output.shape == (batch_size, sam_params['hidden_size'])

    def test_numerical_stability(self, sam_layer, sam_params):
        """
        Ensures forward pass does not generate NaNs or Infs.
        Crucial for distance-based addressing (Sec 2.1).
        """
        batch_size = 4
        x = torch.randn(batch_size, sam_params['input_size'])
        
        output, state = sam_layer(x)
        
        assert not torch.isnan(output).any(), "Output contains NaNs"
        assert not torch.isinf(output).any(), "Output contains Infs"
        
        # Check memory stability
        memory = state[1] 
        assert not torch.isnan(memory).any(), "Memory state contains NaNs"

    def test_sparse_read_invariant(self, sam_layer, sam_params):
        """
        Verifies Section 3.1: The read vector should be a weighted average
        of only K memory words.
        
        We inspect the read weights w_t^R.
        """
        batch_size = 2
        K = sam_params['k_sparse']
        x = torch.randn(batch_size, sam_params['input_size'])
        
        output, state = sam_layer(x)
        
        # Extract read weights from state (assuming implementation exposes them)
        # Shape: (Batch, N)
        read_weights = state[2] # Adjust index based on implementation
        
        # 1. Weights should be non-negative
        assert (read_weights >= 0).all()
        
        # 2. Sparsity check: Count non-zeros
        # Depending on float precision, use a small epsilon
        non_zeros = (read_weights > 1e-6).sum(dim=1)
        
        # The number of non-zero weights should be exactly K (or <= K if using specialized sparse tensors)
        assert (non_zeros <= K).all(), \
            f"Read weights are not sparse! Expected <= {K} non-zeros, got {non_zeros.max()}"

    def test_gradient_flow_and_updates(self, sam_layer, sam_params):
        """
        Verifies backpropagation works and memory is actually updated.
        References Section 3.4 (Efficient BPTT).
        """
        batch_size = 2
        x = torch.randn(batch_size, sam_params['input_size'], requires_grad=True)
        
        # Run forward
        output, state_t1 = sam_layer(x)
        memory_t1 = state_t1[1]
        
        # Run another step to ensure memory update happens
        output_t2, state_t2 = sam_layer(x, state_t1)
        memory_t2 = state_t2[1]
        
        # Check memory changed (Write operation occurred - Sec 3.2)
        assert not torch.allclose(memory_t1, memory_t2), "Memory did not update between steps"
        
        # Check gradients
        loss = output_t2.sum()
        loss.backward()
        
        assert x.grad is not None, "Gradient did not flow back to input"
        
        # Check controller weights have grad
        for param in sam_layer.parameters():
            if param.requires_grad:
                assert param.grad is not None

    def test_overfit_small_sequence(self, sam_params):
        """
        Sanity check: Can SAM learn a trivial identity/copy task?
        Mimics the 'Copy' task from Section 4.2 on a tiny scale.
        """
        test_params = sam_params.copy()
        test_params['hidden_size'] = test_params['input_size']
        
        model = SparseMemoryLayer(**test_params)
        optimizer = optim.Adam(model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()
        
        # Task: Output = Input
        x = torch.randn(4, test_params['input_size'])
        target = x.clone()
        
        state = None
        losses = []
        
        for _ in range(50):
            optimizer.zero_grad()
            output, state = model(x, state)
            
            # Recursively detach nested tuples
            def recursive_detach(s):
                if isinstance(s, torch.Tensor): return s.detach()
                return tuple(recursive_detach(i) for i in s)
            
            state = recursive_detach(state)
            
            loss = criterion(output, target) # Use output projection to match dimensions in real impl
            # For this test, we assume hidden_dim projects to input_dim or we slice
            # Ideally, mock the output projection layer here.
            
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            
        assert losses[-1] < losses[0], "Model failed to reduce loss on trivial task"
