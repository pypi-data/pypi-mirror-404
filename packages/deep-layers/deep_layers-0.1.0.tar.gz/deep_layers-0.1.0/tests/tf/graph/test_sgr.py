import tensorflow as tf
from deep_layers.tf.graph.sgr import SGRLayer
import numpy as np

class TestSGRLayer(tf.test.TestCase):
    """
    Test suite for SGRLayer (TensorFlow)
    Paper: Liang et al., 'Symbolic Graph Reasoning for Semantic Segmentation', NeurIPS 2018.
    """

    def setUp(self):
        super().setUp()
        self.channels = 32
        self.num_nodes = 10
        self.node_dim = 16
        self.vocab_dim = 20
        
        self.adj = np.random.uniform(0, 1, (self.num_nodes, self.num_nodes)).astype(np.float32)
        self.word_embs = np.random.normal(0, 1, (self.num_nodes, self.vocab_dim)).astype(np.float32)
        
        self.layer = SGRLayer(
            num_nodes=self.num_nodes,
            node_feature_dim=self.node_dim,
            adj_matrix=self.adj,
            word_embeddings=self.word_embs
        )
        
        # (Batch, Height, Width, Channels)
        self.input_tensor = tf.random.normal((2, 16, 16, self.channels))

    def test_tf_shape_inference(self):
        """
        Verifies output shape matches input shape (H, W, C) due to residual connection.
        """
        output = self.layer(self.input_tensor)
        self.assertEqual(output.shape, self.input_tensor.shape)

    def test_tf_numerical_stability(self):
        """
        Checks for NaNs resulting from Softmax operations in Eq 2 and 5.
        """
        output = self.layer(self.input_tensor)
        self.assertFalse(np.isnan(output.numpy()).any())
        self.assertFalse(np.isinf(output.numpy()).any())

    def test_tf_gradients_exist(self):
        """
        Ensures the computation graph is connected for backprop.
        """
        with tf.GradientTape() as tape:
            output = self.layer(self.input_tensor)
            loss = tf.reduce_mean(output)
        
        # Get gradients for trainable variables
        grads = tape.gradient(loss, self.layer.trainable_variables)
        
        self.assertGreater(len(grads), 0)
        self.assertTrue(all(g is not None for g in grads))

    def test_tf_train_step(self):
        """
        Tests actual weight updates using an optimizer.
        """
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
        target = tf.random.normal(self.input_tensor.shape)
        
        loss_fn = tf.keras.losses.MeanSquaredError()
        
        initial_loss = loss_fn(target, self.layer(self.input_tensor))

        with tf.GradientTape() as tape:
            preds = self.layer(self.input_tensor)
            loss = loss_fn(target, preds)
        
        grads = tape.gradient(loss, self.layer.trainable_variables)
        optimizer.apply_gradients(zip(grads, self.layer.trainable_variables))
        
        final_loss = loss_fn(target, self.layer(self.input_tensor))
        
        # Should decrease (or at least change)
        self.assertNotEqual(final_loss, initial_loss)

    def test_tf_graph_mode(self):
        """
        Ensures the layer works within a @tf.function (AutoGraph).
        Common failure point for custom layers using explicit tensor manipulation.
        """
        @tf.function
        def run_forward(x):
            return self.layer(x)

        output = run_forward(self.input_tensor)
        self.assertEqual(output.shape, self.input_tensor.shape)

if __name__ == '__main__':
    tf.test.main()
