import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.sequence.mamba import MambaBlock

"""
Test suite for MambaBlock (TensorFlow)
Paper: Gu & Dao, 'Mamba: Linear-Time Sequence Modeling with Selective State Spaces', arXiv:2312.00752.
"""

@pytest.fixture
def d_model():
    return 64

def get_model(d_model):
    """Returns an instance of the Keras Layer."""
    # Replace with your actual initialization
    return MambaBlock(d_model=d_model, d_state=16, d_conv=4, expand=2)

def test_layer_instantiation_and_shape(d_model):
    """
    Verifies the layer can be built and output shape matches (B, L, D).
    """
    layer = get_model(d_model)
    B, L = 2, 50
    x = tf.random.normal((B, L, d_model))
    
    y = layer(x)
    
    assert y.shape == (B, L, d_model)
    assert not np.isnan(y.numpy()).any()

def test_mixed_sequence_lengths(d_model):
    """
    Tests that the layer accepts None in the sequence dimension (L).
    """
    layer = get_model(d_model)
    
    # Input defined with variable length
    inputs = tf.keras.Input(shape=(None, d_model))
    outputs = layer(inputs)
    model = tf.keras.Model(inputs, outputs)
    
    # Run with length 32
    out1 = model(tf.random.normal((1, 32, d_model)))
    assert out1.shape == (1, 32, d_model)
    
    # Run with length 64
    out2 = model(tf.random.normal((1, 64, d_model)))
    assert out2.shape == (1, 64, d_model)

def test_causality_property(d_model):
    """
    Verifies that modifying the end of a sequence does not change
    the predictions at the beginning of the sequence.
    """
    layer = get_model(d_model)
    B, L = 2, 20
    x = tf.random.normal((B, L, d_model))
    
    # 1. Get original output
    y1 = layer(x)
    
    # 2. Modify last timestep
    x_np = x.numpy()
    x_np[:, -1, :] = np.random.randn(B, d_model)
    x_mod = tf.convert_to_tensor(x_np)
    
    y2 = layer(x_mod)
    
    # 3. Compare outputs for t=0 to t=L-2
    # Tolerances might need adjustment based on float32 precision
    diff = np.max(np.abs(y1[:, :-1, :] - y2[:, :-1, :]))
    
    assert diff < 1e-5, f"Causality broken: earlier outputs changed by {diff}"

def test_gradients_exist(d_model):
    """
    Ensures gradients propagate through the Selective Scan mechanics.
    """
    layer = get_model(d_model)
    x = tf.random.normal((2, 10, d_model))
    
    with tf.GradientTape() as tape:
        y = layer(x)
        loss = tf.reduce_sum(y)
        
    grads = tape.gradient(loss, layer.trainable_variables)
    
    assert len(grads) > 0
    for g, v in zip(grads, layer.trainable_variables):
        assert g is not None, f"Gradient for {v.name} is None"
        assert not np.isnan(g.numpy()).any(), f"NaNs in gradient for {v.name}"

def test_overfit_small_batch():
    """
    Simple convergence test on a dummy task.
    """
    d_model = 32
    layer = MambaBlock(d_model=d_model, d_state=8, expand=2)
    
    inputs = tf.keras.Input(shape=(10, d_model))
    outputs = layer(inputs)
    model = tf.keras.Model(inputs, outputs)
    
    model.compile(optimizer='adam', loss='mse')
    
    x = np.random.randn(4, 10, d_model)
    y = np.random.randn(4, 10, d_model) # Random target
    
    history = model.fit(x, y, epochs=10, verbose=0)
    
    loss_start = history.history['loss'][0]
    loss_end = history.history['loss'][-1]
    
    assert loss_end < loss_start
