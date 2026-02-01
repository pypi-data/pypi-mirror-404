import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.phycrnet import PhyCRNetLayer

BATCH_SIZE = 4
CHANNELS = 2
HEIGHT, WIDTH = 128, 128

@pytest.fixture
def model():
    return PhyCRNetLayer(filters=CHANNELS, kernel_size=3)

def test_keras_instantiation_shape(model):
    x = tf.random.normal((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    # Must provide states manually for a Cell call
    h_init = tf.zeros((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    c_init = tf.zeros((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    
    h_next, _ = model(x, [h_init, c_init])
    
    assert h_next.shape == (BATCH_SIZE, HEIGHT, WIDTH, CHANNELS)
    assert not np.isnan(h_next.numpy()).any()

def test_gradient_propagation(model):
    x = tf.random.normal((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    h_init = tf.zeros((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    c_init = tf.zeros((BATCH_SIZE, HEIGHT, WIDTH, CHANNELS))
    
    with tf.GradientTape() as tape:
        tape.watch(x)
        h_next, _ = model(x, [h_init, c_init])
        loss = tf.reduce_mean(tf.square(h_next - x))
        
    grads = tape.gradient(loss, model.trainable_variables)
    assert len(grads) > 0
    assert not all(g is None for g in grads)
    
    with tf.GradientTape() as tape_input:
        tape_input.watch(x)
        h_next, _ = model(x, [h_init, c_init])
        
    grad_input = tape_input.gradient(h_next, x)
    assert grad_input is not None

def test_pixel_shuffle_compatibility(model):
    x_small = tf.random.normal((1, 32, 32, CHANNELS))
    h_init = tf.zeros((1, 32, 32, CHANNELS))
    c_init = tf.zeros((1, 32, 32, CHANNELS))
    
    y_small, _ = model(x_small, [h_init, c_init])
    assert y_small.shape == (1, 32, 32, CHANNELS)

def test_trainability_sanity(model):
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    mse = tf.keras.losses.MeanSquaredError()
    
    x = tf.random.normal((2, 64, 64, CHANNELS))
    target = tf.random.normal((2, 64, 64, CHANNELS))
    h_init = tf.zeros((2, 64, 64, CHANNELS))
    c_init = tf.zeros((2, 64, 64, CHANNELS))
    
    initial_loss = mse(target, model(x, [h_init, c_init])[0])
    
    with tf.GradientTape() as tape:
        y_pred, _ = model(x, [h_init, c_init])
        loss = mse(target, y_pred)
        
    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    
    final_loss = mse(target, model(x, [h_init, c_init])[0])
    assert final_loss.numpy() != initial_loss.numpy()
