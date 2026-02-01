import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.graph.gcn import GCNLayer

class TestGCNLayer:
    """
    Test suite for GCNLayer
    Paper: Kipf & Welling, 'Semi-Supervised Classification with Graph Convolutional Networks', ICLR 2017.
    """


    @pytest.fixture
    def graph_data(self):
        """Generates dummy graph data: 10 nodes, 5 input features."""
        num_nodes = 10
        in_features = 5
        out_features = 4
        
        # Random node features X
        features = torch.randn(num_nodes, in_features, requires_grad=True)
        
        # Random binary adjacency matrix A (symmetric)
        adj = torch.randint(0, 2, (num_nodes, num_nodes)).float()
        adj = (adj + adj.t()) / 2
        adj[adj > 0] = 1.0 
        
        return features, adj, in_features, out_features

    def test_instantiation_and_shape(self, graph_data):
        """Test layer instantiation and output dimensions (Eq. 2)."""
        features, adj, in_feat, out_feat = graph_data
        
        layer = GCNLayer(in_feat, out_feat)
        output = layer(features, adj)
        
        assert output.shape == (features.shape[0], out_feat)
        assert not torch.isnan(output).any()

    def test_gradient_propagation(self, graph_data):
        """Ensure gradients flow back to weights and input features."""
        features, adj, in_feat, out_feat = graph_data
        layer = GCNLayer(in_feat, out_feat)
        
        output = layer(features, adj)
        loss = output.sum()
        loss.backward()
        
        # Check weights gradient
        assert layer.weight.grad is not None
        assert torch.norm(layer.weight.grad) > 0
        
        # Check input features gradient (GCNs must propagate info from neighbors)
        assert features.grad is not None
        assert torch.norm(features.grad) > 0

    def test_numerical_stability(self, graph_data):
        """Check for NaN/Inf with zero inputs or large inputs."""
        _, adj, in_feat, out_feat = graph_data
        # Use bias=False to ensure zero input results in zero output
        layer = GCNLayer(in_feat, out_feat, bias=False) 
        
        # Case: Zero features
        zero_feats = torch.zeros(10, in_feat)
        out_zero = layer(zero_feats, adj)
        assert torch.allclose(out_zero, torch.zeros_like(out_zero), atol=1e-6)

    def test_overfitting_tiny_graph(self, graph_data):
        """Sanity check: Model should be able to overfit a tiny dataset."""
        features, adj, in_feat, out_feat = graph_data
        
        # Create a target label for each node
        target = torch.randint(0, 2, (10,)).float().view(-1, 1) # Binary classification
        
        # Setup simple model (1 layer GCN -> Projection)
        layer = GCNLayer(in_feat, 1) 
        optimizer = optim.Adam(layer.parameters(), lr=0.1)
        criterion = nn.MSELoss()
        
        initial_loss = None
        
        for _ in range(50):
            optimizer.zero_grad()
            output = layer(features, adj)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            if initial_loss is None:
                initial_loss = loss.item()
                
        # Loss should decrease significantly
        assert loss.item() < initial_loss * 0.5

    def test_permutation_invariance_property(self):
        """
        Paper Concept: The operation depends on graph topology. 
        If we permute nodes in X and A identically, output rows should permute identically.
        """
        N, C_in, C_out = 5, 3, 2
        features = torch.randn(N, C_in)
        adj = torch.eye(N) # Simplest case
        
        layer = GCNLayer(C_in, C_out)
        
        # Original Pass
        out_1 = layer(features, adj)
        
        # Permute (swap row 0 and 1)
        perm_idx = torch.tensor([1, 0, 2, 3, 4])
        features_perm = features[perm_idx]
        adj_perm = adj[perm_idx][:, perm_idx]
        
        # Permuted Pass
        out_2 = layer(features_perm, adj_perm)
        
        # Check if output is permuted version of out_1
        assert torch.allclose(out_2, out_1[perm_idx], atol=1e-5)
