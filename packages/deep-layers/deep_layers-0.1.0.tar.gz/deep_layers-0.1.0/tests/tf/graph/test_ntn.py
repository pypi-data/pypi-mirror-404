import tensorflow as tf
from deep_layers.tf.graph.ntn import NTNLayer
import numpy as np

class TestNTNLayer(tf.test.TestCase):
    """
    Test suite for NTNLayer (TensorFlow)
    Paper: Socher et al., 'Reasoning With Neural Tensor Networks for Knowledge Base Completion', NeurIPS 2013.
    """

    # Constants
    BATCH_SIZE = 32
    INPUT_DIM = 100
    SLICE_DIM = 4

    def setUp(self):
        super().setUp()
        self.layer = NTNLayer(output_dim=self.SLICE_DIM, input_dim=self.INPUT_DIM)
        self.e1 = tf.random.normal((self.BATCH_SIZE, self.INPUT_DIM))
        self.e2 = tf.random.normal((self.BATCH_SIZE, self.INPUT_DIM))

    def test_shape_correctness(self):
        """
        Verifies output shape matches (Batch, 1).
        """
        # Keras layers usually take a list for multiple inputs
        output = self.layer([self.e1, self.e2])
        
        self.assertEqual(output.shape.as_list(), [self.BATCH_SIZE, 1])

    def test_numerical_stability_keras(self):
        output = self.layer([self.e1, self.e2])
        
        self.assertFalse(np.any(np.isnan(output.numpy())), "Output contains NaNs")
        self.assertFalse(np.any(np.isinf(output.numpy())), "Output contains Infs")

    def test_gradient_flow(self):
        """
        Checks that gradients can be computed with respect to inputs and weights.
        """
        with tf.GradientTape() as tape:
            tape.watch([self.e1, self.e2])
            output = self.layer([self.e1, self.e2])
            loss = tf.reduce_mean(output)
            
        grads = tape.gradient(loss, list(self.layer.trainable_variables) + [self.e1, self.e2])
        
        # Ensure at least some gradients are non-zero
        self.assertTrue(any(g is not None for g in grads), "Gradients are None")
        # Check that we have gradients for the Tensor (W), Standard (V), Bias (b), and U
        self.assertGreaterEqual(len(self.layer.trainable_variables), 4) 

    def test_model_trainability(self):
        """
        Integration test: Can the layer fit a dummy target in a compiled model?
        """
        # Create a simple functional model
        input_e1 = tf.keras.Input(shape=(self.INPUT_DIM,))
        input_e2 = tf.keras.Input(shape=(self.INPUT_DIM,))
        
        layer_inst = NTNLayer(output_dim=self.SLICE_DIM, input_dim=self.INPUT_DIM)
        score = layer_inst([input_e1, input_e2])
        
        model = tf.keras.Model(inputs=[input_e1, input_e2], outputs=score)
        model.compile(optimizer='adam', loss='mse')
        
        # Dummy data
        x1 = np.random.randn(10, self.INPUT_DIM).astype(np.float32)
        x2 = np.random.randn(10, self.INPUT_DIM).astype(np.float32)
        y = np.ones((10, 1)).astype(np.float32) # Try to predict 1.0
        
        history = model.fit([x1, x2], y, epochs=20, verbose=0)
        
        loss_start = history.history['loss'][0]
        loss_end = history.history['loss'][-1]
        
        self.assertLess(loss_end, loss_start, "Loss did not decrease during training")

    def test_config_serialization(self):
        """
        Keras specific: Ensure the layer can be serialized (get_config).
        Important for saving/loading models with custom layers.
        """
        config = self.layer.get_config()
        layer_from_config = NTNLayer.from_config(config)
        
        self.assertEqual(config['input_dim'], self.INPUT_DIM)
        self.assertEqual(config['output_dim'], self.SLICE_DIM)
        self.assertIsInstance(layer_from_config, NTNLayer)

if __name__ == '__main__':
    tf.test.main()
