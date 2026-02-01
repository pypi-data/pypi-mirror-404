import tensorflow as tf
from tensorflow import keras
from deep_layers.tf.graph.set_transformer import SAB, PMA
import numpy as np

class TestSetTransformer(tf.test.TestCase):
    """
    Test suite for SetTransformer (TensorFlow)
    Paper: Lee et al., 'Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks', ICML 2019.
    """
    def test_instantiation_and_shape_sab(self):
        """Test SAB (Encoder) Shape preservation."""
        B, N, D = 4, 15, 32
        layer = SAB(d_model=D, n_heads=4)
        
        x = tf.random.normal((B, N, D))
        out = layer(x)
        
        self.assertEqual(out.shape, (B, N, D))

    def test_instantiation_and_shape_pma(self):
        """Test PMA (Decoder) aggregation to k seeds."""
        B, N, D = 4, 20, 64
        k = 3
        layer = PMA(d_model=D, n_heads=4, k=k)
        
        x = tf.random.normal((B, N, D))
        out = layer(x)
        
        # Should result in k vectors per batch
        self.assertEqual(out.shape, (B, k, D))

    def test_permutation_equivariance(self):
        """
        SAB should be equivariant.
        Shuffling input axis 1 should result in shuffled output axis 1.
        """
        B, N, D = 2, 10, 16
        layer = SAB(d_model=D, n_heads=2)
        
        x = tf.random.normal((B, N, D))
        
        # Forward pass 1
        out_original = layer(x)
        
        # Create permutation
        indices = tf.range(start=0, limit=N, dtype=tf.int32)
        shuffled_indices = tf.random.shuffle(indices)
        
        # Shuffle input
        x_shuffled = tf.gather(x, shuffled_indices, axis=1)
        
        # Forward pass 2
        out_shuffled_input = layer(x_shuffled)
        
        # Shuffle the output of pass 1 to compare
        out_original_shuffled = tf.gather(out_original, shuffled_indices, axis=1)
        
        diff = tf.reduce_max(tf.abs(out_original_shuffled - out_shuffled_input))
        self.assertLess(diff, 1e-4)

    def test_permutation_invariance_pma(self):
        """
        PMA should be invariant to input set order.
        """
        B, N, D = 2, 10, 16
        # k=1 is standard "global pooling" equivalent
        layer = PMA(d_model=D, n_heads=2, k=1)
        
        x = tf.random.normal((B, N, D))
        x_reversed = tf.reverse(x, axis=[1])
        
        out_1 = layer(x)
        out_2 = layer(x_reversed)
        
        diff = tf.reduce_max(tf.abs(out_1 - out_2))
        self.assertLess(diff, 1e-5)

    def test_variable_set_size(self):
        """
        Keras models should handle None in the shape definition for the set dimension.
        """
        D = 32
        # Define functional model with variable input shape
        inputs = keras.Input(shape=(None, D))
        x = SAB(d_model=D, n_heads=4)(inputs)
        model = keras.Model(inputs, x)
        
        # N=10
        x1 = tf.random.normal((1, 10, D))
        out1 = model(x1)
        self.assertEqual(out1.shape[1], 10)
        
        # N=50
        x2 = tf.random.normal((1, 50, D))
        out2 = model(x2)
        self.assertEqual(out2.shape[1], 50)

    def test_training_gradients(self):
        """
        Ensure gradients propagate through the attention mechanism and 
        to the learnable parameters (like inducing points I or seeds S).
        """
        B, N, D = 4, 10, 16
        layer = PMA(d_model=D, n_heads=2, k=1)
        
        x = tf.random.normal((B, N, D))
        
        with tf.GradientTape() as tape:
            tape.watch(x)
            out = layer(x)
            loss = tf.reduce_mean(out)
        
        grads = tape.gradient(loss, layer.trainable_variables)
        
        # Check that we have gradients for weights (Seed vector S is trainable)
        self.assertGreater(len(grads), 0)
        # Ensure no None gradients
        self.assertFalse(any(g is None for g in grads))
        # Ensure no NaN
        self.assertFalse(tf.math.reduce_any(tf.math.is_nan(out)))

if __name__ == '__main__':
    tf.test.main()
