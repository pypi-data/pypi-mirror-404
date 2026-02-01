import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.vision.coord_conv import CoordConv

"""
Test suite for CoordConv (TensorFlow)
Paper: Liu et al., 'An Intriguing Failing of Convolutional Neural Networks and the CoordConv Solution', NeurIPS 2018.
"""

@pytest.mark.parametrize("with_r", [True, False])
def test_keras_instantiation_and_shape(with_r):
    """
    Verifies shape logic. Assumes channels_last (N, H, W, C) default in TF.
    """
    batch, h, w, in_c = 2, 28, 28, 3
    out_c = 10
    
    layer = CoordConv(filters=out_c, kernel_size=3, with_r=with_r)
    
    x = tf.random.normal((batch, h, w, in_c))
    out = layer(x)
    
    # Expectation for valid padding (default in Keras usually)
    expected_dim = h - 2 
    assert out.shape == (batch, expected_dim, expected_dim, out_c)

def test_keras_numerical_stability():
    """Checks for numeric anomalies."""
    layer = CoordConv(filters=4, kernel_size=3, padding='same')
    x = tf.random.normal((1, 32, 32, 3))
    out = layer(x)
    
    assert not np.any(np.isnan(out.numpy()))
    assert not np.any(np.isinf(out.numpy()))

def test_keras_coord_injection_invariant():
    """
    Paper Specific Test: 
    Input of zeros should produce non-zeros due to coordinate channels [-1, 1].
    """
    # use_bias=False ensures standard conv output would be zero
    layer = CoordConv(filters=1, kernel_size=1, use_bias=False)
    
    # Build layer to init weights
    x = tf.zeros((1, 10, 10, 1))
    _ = layer(x) 
    
    # Set weights to ones manually to guarantee coord channels are picked up
    # Shape logic: 1x1 kernel, input_channels (1) + coords (2) = 3 total input channels
    weights = [tf.ones_like(w) for w in layer.weights] 
    layer.set_weights(weights)
    
    out = layer(x)
    
    # Assert output is not dead zero
    assert tf.reduce_sum(tf.abs(out)) > 0.0

def test_keras_trainability():
    """
    Verifies that the layer is differentiable and trainable within a GradientTape.
    """
    layer = CoordConv(filters=2, kernel_size=3, padding='same')
    x = tf.random.normal((4, 16, 16, 3))
    y_true = tf.random.normal((4, 16, 16, 2))
    
    with tf.GradientTape() as tape:
        y_pred = layer(x)
        loss = tf.reduce_mean(tf.square(y_pred - y_true))
        
    grads = tape.gradient(loss, layer.trainable_variables)
    
    # Check gradients exist
    assert len(grads) > 0
    assert all(g is not None for g in grads)
    
    # Apply gradients check
    optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)
    old_weights = [tf.identity(w) for w in layer.trainable_variables]
    
    optimizer.apply_gradients(zip(grads, layer.trainable_variables))
    
    # Verify weights changed
    for old, new in zip(old_weights, layer.trainable_variables):
        assert not np.allclose(old.numpy(), new.numpy()), "Weights did not update"
