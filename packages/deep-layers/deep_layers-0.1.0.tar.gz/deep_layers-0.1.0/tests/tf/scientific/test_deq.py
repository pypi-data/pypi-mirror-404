import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.deq import DEQLayer

class MockCell(tf.keras.layers.Layer):
    def __init__(self, hidden_dim, **kwargs):
        super().__init__(**kwargs)
        self.dense_z = tf.keras.layers.Dense(hidden_dim, use_bias=False)
        self.dense_x = tf.keras.layers.Dense(hidden_dim)

    def build(self, input_shape):
        super().build(input_shape)

    def call(self, inputs):
        z, x = inputs
        return tf.nn.tanh(self.dense_z(z) + self.dense_x(x))

    def get_config(self):
        return super().get_config()

def test_keras_instantiation_shapes():
    batch, seq_len, dim = 4, 10, 8
    cell = MockCell(hidden_dim=dim)
    layer = DEQLayer(cell)
    inputs = tf.random.normal((batch, seq_len, dim))
    z_star = layer(inputs)
    assert z_star.shape == (batch, seq_len, dim)

def test_keras_fixed_point_invariant():
    dim = 8
    cell = MockCell(hidden_dim=dim)
    layer = DEQLayer(cell)
    inputs = tf.random.normal((2, 5, dim))
    z_star = layer(inputs)
    f_z_star = cell((z_star, inputs))
    assert tf.norm(f_z_star - z_star) < 1e-3

def test_keras_gradient_flow():
    dim = 8
    cell = MockCell(hidden_dim=dim)
    layer = DEQLayer(cell)
    inputs = tf.random.normal((2, 5, dim))
    with tf.GradientTape() as tape:
        tape.watch(inputs)
        z_star = layer(inputs)
        loss = tf.reduce_sum(z_star)
    grads = tape.gradient(loss, layer.trainable_variables)
    assert len(grads) > 0
    assert tf.norm(grads[0]) > 0.0

def test_keras_serialization():
    dim = 8
    cell = MockCell(hidden_dim=dim)
    layer = DEQLayer(cell)
    config = layer.get_config()
    assert 'f_layer' in config

def test_keras_training_loop():
    dim = 4
    cell = MockCell(hidden_dim=dim)
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(5, dim)),
        DEQLayer(cell)
    ])
    model.compile(optimizer='adam', loss='mse')
    x = tf.random.normal((10, 5, dim))
    y = tf.nn.tanh(x)
    history = model.fit(x, y, epochs=5, verbose=0)
    assert history.history['loss'][-1] < history.history['loss'][0]
