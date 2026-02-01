import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.vision.dropblock import DropBlock

@pytest.fixture
def layer_cls():
    return DropBlock

def test_instantiation_and_shape(layer_cls):
    layer = layer_cls(block_size=3, keep_prob=0.9)
    inputs = tf.random.normal((4, 32, 32, 16))
    outputs = layer(inputs, training=True)
    assert outputs.shape == (4, 32, 32, 16)
    assert np.isclose(layer.drop_prob, 0.1)

def test_inference_mode_identity(layer_cls):
    layer = layer_cls(block_size=3, keep_prob=0.5)
    inputs = tf.random.normal((2, 10, 10, 3))
    outputs = layer(inputs, training=False)
    np.testing.assert_allclose(inputs.numpy(), outputs.numpy())

def test_training_mode_drops_values(layer_cls):
    layer = layer_cls(block_size=3, keep_prob=0.1)
    inputs = tf.ones((2, 20, 20, 3))
    outputs = layer(inputs, training=True)
    assert np.any(outputs.numpy() == 0.0)

def test_numerical_stability(layer_cls):
    layer = layer_cls(block_size=3, keep_prob=0.5)
    inputs = tf.random.normal((4, 16, 16, 8))
    outputs = layer(inputs, training=True)
    assert not np.isnan(outputs.numpy()).any()

def test_gradient_propagation(layer_cls):
    layer = layer_cls(block_size=3, keep_prob=0.5)
    inputs = tf.random.normal((2, 10, 10, 3))
    with tf.GradientTape() as tape:
        tape.watch(inputs)
        loss = tf.reduce_sum(layer(inputs, training=True))
    grads = tape.gradient(loss, inputs)
    assert grads is not None and tf.reduce_sum(tf.abs(grads)) > 0

def test_normalization_scaling(layer_cls):
    inputs = tf.ones((10, 50, 50, 3))
    layer = layer_cls(block_size=5, keep_prob=0.75)
    outputs = layer(inputs, training=True)
    assert np.isclose(tf.reduce_mean(inputs), tf.reduce_mean(outputs), rtol=0.2)

def test_overfit_trainability(layer_cls):
    # Fixed seed and more epochs for stability
    tf.random.set_seed(42)
    x = tf.random.normal((16, 8, 8, 3))
    # Target is simple: sum of channels
    y = tf.cast(tf.reduce_mean(x, axis=[1, 2, 3]) > 0, tf.float32)
    
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(8, 8, 3)),
        layer_cls(block_size=2, keep_prob=0.9),
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss='binary_crossentropy')
    
    initial_loss = model.evaluate(x, y, verbose=0)
    history = model.fit(x, y, epochs=25, verbose=0) 
    final_loss = history.history['loss'][-1]
    
    assert final_loss < initial_loss
