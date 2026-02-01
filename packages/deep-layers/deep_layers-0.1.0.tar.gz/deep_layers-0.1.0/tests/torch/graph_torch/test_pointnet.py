import pytest
import torch
import torch.nn as nn
import torch.optim as optim
from tests.common import assert_no_nan_inf

from deep_layers.torch.graph.pointnet import PointNetSA

class TestPointNetSA:
    """
    Test suite for PointNetSA
    Paper: Qi et al., 'PointNet++: Deep Hierarchical Feature Learning on Point Sets', NeurIPS 2017.
    """

    # Constants based on PointNet++ architectures (e.g., SSG)
    BATCH_SIZE = 4
    NUM_POINTS_IN = 1024
    NUM_POINTS_OUT = 256  # N' in paper
    IN_CHANNELS = 32      # C in paper
    XYZ_DIM = 3           # d in paper
    RADIUS = 0.2
    NSAMPLE = 32          # K in paper
    MLP_CHANNELS = [32, 64, 128] # MLP specs

    @pytest.fixture
    def sa_layer(self):
        """Instantiates a standard Set Abstraction (SSG) layer."""
        # in_channel should be the dimension of the feature tensor only.
        # The layer internally adds 3 channels for relative coordinates.
        return PointNetSA(
            npoint=self.NUM_POINTS_OUT,
            radius=self.RADIUS,
            nsample=self.NSAMPLE,
            in_channel=self.IN_CHANNELS, 
            mlp=self.MLP_CHANNELS,
            group_all=False
        )

    @pytest.fixture
    def input_data(self, device):
        """Generates random point cloud data: XYZ and Features."""
        xyz = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM).to(device)
        features = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS).to(device)
        return xyz, features

    @pytest.mark.parametrize("device", ["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"])
    def test_sa_layer_output_shapes(self, sa_layer, input_data, device):
        """
        Validates the transformation from N points to N' centroids.
        """
        sa_layer = sa_layer.to(device)
        xyz, features = input_data
        
        new_xyz, new_features = sa_layer(xyz, features)

        # Check XYZ shape: (B, N', 3)
        assert new_xyz.shape == (self.BATCH_SIZE, self.NUM_POINTS_OUT, self.XYZ_DIM)
        
        # Check Feature shape: (B, N', Output_Channel)
        expected_feat_dim = self.MLP_CHANNELS[-1]
        assert new_features.shape == (self.BATCH_SIZE, self.NUM_POINTS_OUT, expected_feat_dim)

    def test_numerical_stability(self, sa_layer):
        """Checks for NaNs or Infs during forward pass."""
        xyz = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM)
        features = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS)
        
        new_xyz, new_features = sa_layer(xyz, features)
        
        assert not torch.isnan(new_features).any(), "Output contains NaNs"
        assert not torch.isinf(new_features).any(), "Output contains Infs"
        assert not torch.isnan(new_xyz).any(), "Output coordinates contain NaNs"

    def test_gradient_propagation(self, sa_layer):
        """
        Verifies that gradients flow back to both input features and input coordinates.
        """
        xyz = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM, requires_grad=True)
        features = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS, requires_grad=True)
        
        new_xyz, new_features = sa_layer(xyz, features)
        loss = new_features.sum() + new_xyz.sum()
        loss.backward()
        
        assert xyz.grad is not None, "Gradients did not flow back to input XYZ"
        assert features.grad is not None, "Gradients did not flow back to input Features"
        assert torch.abs(features.grad).sum() > 0, "Gradients are zero for features"

    def test_batch_independence(self, sa_layer):
        """
        Ensures that processing for sample i in a batch does not affect sample j.
        """
        sa_layer.eval()
        xyz = torch.randn(2, self.NUM_POINTS_IN, self.XYZ_DIM)
        features = torch.randn(2, self.NUM_POINTS_IN, self.IN_CHANNELS)
        
        # Run batch together
        out_xyz_batch, out_feat_batch = sa_layer(xyz, features)
        
        # Run single sample
        out_xyz_single, out_feat_single = sa_layer(xyz[0:1], features[0:1])
        
        # Compare
        torch.testing.assert_close(out_feat_batch[0], out_feat_single[0], atol=1e-5, rtol=1e-5)

    def test_overfit_small_batch(self, sa_layer):
        """
        Sanity check: Can a single layer learn to map a specific input to zero?
        """
        optimizer = torch.optim.Adam(sa_layer.parameters(), lr=0.01)
        xyz = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM)
        features = torch.randn(self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS)
        target = torch.zeros(self.BATCH_SIZE, self.NUM_POINTS_OUT, self.MLP_CHANNELS[-1])

        sa_layer.train()
        
        initial_loss = None
        for i in range(10):
            optimizer.zero_grad()
            _, output = sa_layer(xyz, features)
            loss = torch.nn.functional.mse_loss(output, target)
            loss.backward()
            optimizer.step()
            
            if i == 0: initial_loss = loss.item()
            final_loss = loss.item()

        assert final_loss < initial_loss, "Loss did not decrease"
