import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.kan import KANLayer

@pytest.mark.parametrize("batch_size", [1, 32])
def test_layer_call_and_shape(batch_size):
    in_feat, out_feat = 8, 4
    inputs = tf.keras.Input(shape=(in_feat,))
    layer = KANLayer(in_features=in_feat, out_features=out_feat, grid_size=5)
    outputs = layer(inputs)
    model = tf.keras.Model(inputs, outputs)
    x = tf.random.normal((batch_size, in_feat))
    y = model(x)
    assert y.shape == (batch_size, out_feat)

def test_serialization_config():
    layer = KANLayer(in_features=5, out_features=10, grid_size=7)
    config = layer.get_config()
    assert config['out_features'] == 10
    new_layer = KANLayer.from_config(config)
    assert new_layer.grid_size == 7

def test_trainable_variables_exist():
    layer = KANLayer(in_features=5, out_features=4, grid_size=5)
    x = tf.random.normal((2, 5))
    _ = layer(x)
    assert len(layer.trainable_weights) > 0

def test_fit_simple_nonlinearity():
    tf.random.set_seed(42)
    X = np.random.uniform(-1, 1, (200, 2)).astype(np.float32)
    y = np.sin(np.pi * X[:, 0:1]) + X[:, 1:2]**2
    inputs = tf.keras.Input(shape=(2,))
    x = KANLayer(in_features=2, out_features=8, grid_size=5)(inputs)
    outputs = tf.keras.layers.Dense(1)(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer='adam', loss='mse')
    history = model.fit(X, y, epochs=20, verbose=0)
    assert history.history['loss'][-1] < history.history['loss'][0] * 0.8

def test_mixed_precision_support():
    try:
        tf.keras.backend.set_floatx('float64')
        # Pass dtype explicitly to layer to ensure weights are created as float64
        layer = KANLayer(in_features=4, out_features=2, dtype='float64')
        x = tf.random.normal((4, 4), dtype=tf.float64)
        out = layer(x)
        assert out.dtype == tf.float64
    finally:
        tf.keras.backend.set_floatx('float32')
