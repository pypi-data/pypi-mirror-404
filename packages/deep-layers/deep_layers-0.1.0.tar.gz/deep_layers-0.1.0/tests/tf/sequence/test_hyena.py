import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.sequence.hyena import HyenaOperator

"""
Test suite for HyenaOperator (TensorFlow)
Paper: Poli et al., 'Hyena Hierarchy: Towards Larger Convolutional Language Models', ICML 2023.
"""

@pytest.fixture
def hyena_config():
    return {
        "d_model": 64,
        "l_max": 128,
        "order": 2
    }

@pytest.fixture
def layer(hyena_config):
    return HyenaOperator(**hyena_config)

def test_keras_shape_and_inference(layer, hyena_config):
    """Check tensor shapes and execution."""
    B, L, D = 4, hyena_config['l_max'], hyena_config['d_model']
    x = tf.random.normal((B, L, D))
    
    y = layer(x)
    
    assert y.shape == (B, L, D)
    assert not np.any(np.isnan(y.numpy()))

def test_keras_causality(layer, hyena_config):
    """
    Verifies autoregressive property. 
    Paper Section 3.3: 'Causality can be guaranteed by parametrizing causal convolutions.'
    """
    B, L, D = 2, 64, hyena_config['d_model']
    x = tf.random.normal((B, L, D))
    
    # Run original
    y_orig = layer(x)
    
    # Modify last time step
    noise = tf.random.normal((B, 1, D))
    x_mod = tf.concat([x[:, :-1, :], noise], axis=1)
    
    y_mod = layer(x_mod)
    
    # Compare t=0 to t=L-2 (should be equal)
    diff = tf.reduce_sum(tf.abs(y_orig[:, :-1, :] - y_mod[:, :-1, :]))
    
    assert diff < 1e-4, "Causality check failed: Past outputs changed based on future input."

def test_keras_gradients(layer, hyena_config):
    """Check gradient flow through FFT ops."""
    B, L, D = 2, 32, hyena_config['d_model']
    x = tf.random.normal((B, L, D))
    
    with tf.GradientTape() as tape:
        tape.watch(x)
        y = layer(x)
        loss = tf.reduce_sum(y)
        
    grads = tape.gradient(loss, layer.trainable_variables)
    
    # Ensure gradients exist and are finite
    assert len(grads) > 0
    for g in grads:
        assert g is not None
        assert not np.any(np.isnan(g.numpy()))

def test_keras_serialization(layer, hyena_config):
    """
    Hyena contains complex internal state (FFT params, projections).
    Ensure it can be saved/loaded.
    """
    input_shape = (hyena_config['l_max'], hyena_config['d_model'])
    inputs = tf.keras.Input(shape=input_shape)
    outputs = layer(inputs)
    model = tf.keras.Model(inputs, outputs)
    
    # Test config
    config = layer.get_config()
    new_layer = HyenaOperator.from_config(config)
    
    assert new_layer.d_model == layer.d_model

def test_trainability(layer, hyena_config):
    """Train overfitting test."""
    B, L, D = 2, 32, hyena_config['d_model']
    x = tf.random.normal((B, L, D))
    y_true = tf.random.normal((B, L, D))
    
    inputs = tf.keras.Input(shape=(L, D))
    outputs = layer(inputs)
    model = tf.keras.Model(inputs, outputs)
    
    model.compile(optimizer='adam', loss='mse')
    
    history = model.fit(x, y_true, epochs=10, verbose=0)
    
    assert history.history['loss'][-1] < history.history['loss'][0]
