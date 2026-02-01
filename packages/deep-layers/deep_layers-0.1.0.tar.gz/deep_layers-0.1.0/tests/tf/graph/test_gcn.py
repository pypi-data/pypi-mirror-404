import tensorflow as tf
from deep_layers.tf.graph.gcn import GCNLayer
import numpy as np

class TestGCNLayer(tf.test.TestCase):
    """
    Test suite for GCNLayer (TensorFlow)
    Paper: Kipf & Welling, 'Semi-Supervised Classification with Graph Convolutional Networks', ICLR 2017.
    """

    def setUp(self):
        super().setUp()
        self.num_nodes = 10
        self.in_features = 5
        self.out_features = 4
        
        # Random features
        self.features = tf.random.normal((self.num_nodes, self.in_features))
        
        # Random Adjacency
        adj = tf.random.uniform((self.num_nodes, self.num_nodes), minval=0, maxval=2, dtype=tf.int32)
        self.adj = tf.cast(adj, tf.float32)

    def test_tf_instantiation_and_shape(self):
        """Test Keras layer output shape (N, F_out)."""
        # Keras GCNs usually take a list [features, adjacency]
        layer = GCNLayer(units=self.out_features)
        output = layer([self.features, self.adj])
        
        self.assertEqual(output.shape, (self.features.shape[0], self.out_features))
        self.assertFalse(np.any(np.isnan(output.numpy())))

    def test_tf_backprop(self):
        """Test gradient computation in GradientTape."""
        layer = GCNLayer(units=self.out_features)
        
        with tf.GradientTape() as tape:
            tape.watch(self.features)
            output = layer([self.features, self.adj])
            loss = tf.reduce_sum(output)
        
        # Check gradients w.r.t trainable variables (Weights) and Input (X)
        grads = tape.gradient(loss, list(layer.trainable_variables) + [self.features])
        
        # Weights gradient check
        self.assertGreater(len(grads), 0)
        self.assertIsNotNone(grads[0]) # Weight matrix
        
        # Input feature gradient check (last item in list)
        self.assertIsNotNone(grads[-1]) 

    def test_tf_renormalization_trick_logic(self):
        """
        Test Eq 8: Z = D_tilde^-0.5 * A_tilde * D_tilde^-0.5 * X * Theta
        If A is zero matrix, A_tilde becomes I (due to A+I).
        The layer should act as a simple Dense layer scaled by self-loop degree.
        """
        num_nodes = self.features.shape[0]
        
        # Zero adjacency + self-loops -> Effectively A_tilde = I
        adj_id = tf.eye(num_nodes)
        
        layer = GCNLayer(units=self.out_features, use_bias=False)
        output = layer([self.features, adj_id])
        
        # Manually calculate dense projection XW
        weights = layer.trainable_variables[0]
        expected_projection = tf.matmul(self.features, weights)
        
        # If standard renormalization (D=I), result should be close to XW
        correlation = np.corrcoef(output.numpy().flatten(), 
                                expected_projection.numpy().flatten())[0,1]
        self.assertGreater(correlation, 0.99)

    def test_tf_overfit_loop(self):
        """Ensure minimal trainability on random targets."""
        target = tf.random.normal((self.features.shape[0], self.out_features))
        
        layer = GCNLayer(units=self.out_features)
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
        
        initial_loss = None
        final_loss = None
        
        for i in range(20):
            with tf.GradientTape() as tape:
                out = layer([self.features, self.adj])
                loss = tf.reduce_mean(tf.square(out - target))
            
            grads = tape.gradient(loss, layer.trainable_variables)
            optimizer.apply_gradients(zip(grads, layer.trainable_variables))
            
            if i == 0: initial_loss = loss.numpy()
            final_loss = loss.numpy()
            
        self.assertLess(final_loss, initial_loss)

if __name__ == '__main__':
    tf.test.main()
