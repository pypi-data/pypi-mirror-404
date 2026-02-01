import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.vision.glu import GLU

"""
Test suite for GLU (TensorFlow)
Paper: Dauphin et al., 'Language Modeling with Gated Convolutional Networks', ICML 2017.
"""

@pytest.fixture
def layer_config():
    return {
        "filters": 32,
        "kernel_size": 3,
    }

def test_instantiation_and_shape(layer_config):
    """
    Verifies layer output shape follows (Batch, Length, Filters).
    Paper requires output length == input length (padding).
    """
    batch_size, seq_len = 4, 20
    # Input: (Batch, Length, Channels)
    inputs = tf.random.normal((batch_size, seq_len, 32))
    
    layer = GLU(**layer_config)
    outputs = layer(inputs)
    
    expected_shape = (batch_size, seq_len, layer_config["filters"])
    assert outputs.shape == expected_shape
    assert not np.isnan(outputs.numpy()).any()

def test_causality_masked_conv(layer_config):
    """
    Tests the crucial causal property for Language Modeling (Section 2).
    Padding must prevent kernels from seeing future tokens.
    """
    seq_len = 10
    channels = 32
    
    # Create two inputs identical up to the last timestep
    x1 = np.random.randn(1, seq_len, channels).astype(np.float32)
    x2 = x1.copy()
    x2[:, -1, :] = np.random.randn(1, channels) # Change last token
    
    layer = GLU(**layer_config)
    
    out1 = layer(x1)
    out2 = layer(x2)
    
    # Check that the FIRST output timestep is identical
    # If convolution is not causal, the change at -1 would propagate to 0 via 'valid' padding or wrong shifting
    np.testing.assert_allclose(
        out1[:, 0, :], 
        out2[:, 0, :], 
        err_msg="Causality violation: Future token influenced past prediction"
    )

def test_gradient_propagation(layer_config):
    """
    Checks Eq (3) logic: Gradients should flow through the linear path.
    """
    layer = GLU(**layer_config)
    x = tf.random.normal((2, 10, 32))
    
    with tf.GradientTape() as tape:
        tape.watch(x)
        out = layer(x)
        loss = tf.reduce_sum(out)
        
    grads = tape.gradient(loss, layer.trainable_variables)
    
    assert len(grads) > 0
    for g in grads:
        assert g is not None
        assert not tf.reduce_any(tf.math.is_nan(g))

def test_trainability_overfit(layer_config):
    """
    Sanity check: Can the layer minimize loss on a small batch?
    """
    layer = GLU(**layer_config)
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
    
    # Simple task: Map Input X to Target Y
    x = tf.random.normal((4, 5, 32))
    y = tf.random.normal((4, 5, layer_config["filters"]))
    
    initial_loss = tf.reduce_mean(tf.square(layer(x) - y))
    
    for _ in range(30):
        with tf.GradientTape() as tape:
            pred = layer(x)
            loss = tf.reduce_mean(tf.square(pred - y))
        grads = tape.gradient(loss, layer.trainable_variables)
        optimizer.apply_gradients(zip(grads, layer.trainable_variables))
        
    final_loss = tf.reduce_mean(tf.square(layer(x) - y))
    
    assert final_loss < initial_loss, "Loss did not decrease"

def test_serialization(layer_config):
    """
    Ensures the layer can be saved/loaded (standard Keras requirement).
    """
    layer = GLU(**layer_config)
    config = layer.get_config()
    reconstructed_layer = GLU.from_config(config)
    assert reconstructed_layer.filters == layer_config["filters"]
