import tensorflow as tf
from deep_layers.tf.graph.pointnet import PointNetSA
import numpy as np

class TestPointNetSA(tf.test.TestCase):
    """
    Test suite for PointNetSA (TensorFlow)
    Paper: Qi et al., 'PointNet++: Deep Hierarchical Feature Learning on Point Sets', NeurIPS 2017.
    """

    # Constants
    BATCH_SIZE = 4
    NUM_POINTS_IN = 1024
    NUM_POINTS_OUT = 256
    IN_CHANNELS = 32
    XYZ_DIM = 3
    MLP_CHANNELS = [32, 64, 128]

    def setUp(self):
        super().setUp()
        self.sa_layer = PointNetSA(
            npoint=self.NUM_POINTS_OUT,
            radius=0.2,
            nsample=32,
            mlp_list=self.MLP_CHANNELS
        )

    def test_sa_layer_instantiation(self):
        """Checks basic instantiation."""
        self.assertIsInstance(self.sa_layer, tf.keras.layers.Layer)

    def test_sa_layer_shapes(self):
        """
        Validates output tensor shapes.
        Inputs: [xyz_tensor, features_tensor]
        """
        xyz = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM))
        features = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS))
        
        # Call layer
        new_xyz, new_features = self.sa_layer([xyz, features])
        
        # Check XYZ shape (Batch, N', 3)
        self.assertEqual(new_xyz.shape.as_list(), [self.BATCH_SIZE, self.NUM_POINTS_OUT, self.XYZ_DIM])
        
        # Check Feature shape (Batch, N', C')
        expected_channels = self.MLP_CHANNELS[-1]
        self.assertEqual(new_features.shape.as_list(), [self.BATCH_SIZE, self.NUM_POINTS_OUT, expected_channels])

    def test_numerical_stability(self):
        """Checks for NaNs/Infs in the output."""
        xyz = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM))
        features = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS))
        
        _, new_features = self.sa_layer([xyz, features])
        
        self.assertFalse(np.isnan(new_features.numpy()).any())
        self.assertFalse(np.isinf(new_features.numpy()).any())

    def test_gradient_flow(self):
        """
        Ensures gradients exist for trainable weights.
        """
        xyz = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM))
        features = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS))
        
        with tf.GradientTape() as tape:
            _, output = self.sa_layer([xyz, features])
            loss = tf.reduce_mean(output)
            
        gradients = tape.gradient(loss, self.sa_layer.trainable_variables)
        
        # Ensure we have gradients and they are not all None
        self.assertGreater(len(gradients), 0)
        self.assertTrue(any(g is not None for g in gradients))

    def test_training_step(self):
        """
        Mini integration test: Can the layer fit random data?
        """
        xyz = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM))
        features = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.IN_CHANNELS))
        
        # Create a simple model wrapper for compilation
        inputs_xyz = tf.keras.Input(shape=(self.NUM_POINTS_IN, self.XYZ_DIM))
        inputs_feat = tf.keras.Input(shape=(self.NUM_POINTS_IN, self.IN_CHANNELS))
        
        out_xyz, out_feat = self.sa_layer([inputs_xyz, inputs_feat])
        # Flatten for simple loss calculation
        x = tf.keras.layers.GlobalAveragePooling1D()(out_feat)
        outputs = tf.keras.layers.Dense(1)(x)
        
        model = tf.keras.Model(inputs=[inputs_xyz, inputs_feat], outputs=outputs)
        model.compile(optimizer='adam', loss='mse')
        
        # Random targets
        y = tf.random.normal((self.BATCH_SIZE, 1))
        
        history = model.fit([xyz, features], y, epochs=5, verbose=0)
        losses = history.history['loss']
        
        self.assertLess(losses[-1], losses[0], "Loss failed to decrease during training")

    def test_sparse_input_edge_case(self):
        """
        Paper Edge Case: Handling non-uniform density / sparse regions.
        Though typically handled via radius masking, the layer should not crash 
        if points are effectively zeroed out or very distant.
        """
        xyz = tf.random.normal((self.BATCH_SIZE, self.NUM_POINTS_IN, self.XYZ_DIM))
        # Create outliers by scaling up a portion of the cloud to be far away
        outliers = xyz * 100.0
        
        _, new_features = self.sa_layer([outliers, tf.zeros_like(outliers)])
        
        self.assertEqual(new_features.shape.as_list()[1], self.NUM_POINTS_OUT)
        self.assertFalse(np.isnan(new_features.numpy()).any())

if __name__ == '__main__':
    tf.test.main()
