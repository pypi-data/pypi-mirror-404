import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.vision.involution import Involution

TEST_CONFIGS = [
    (16, 3, 1, 2),
    (32, 5, 2, 4),
]

@pytest.mark.parametrize("C, K, S, r", TEST_CONFIGS)
def test_shape_and_inference(C, K, S, r):
    layer = Involution(channels=C, kernel_size=K, stride=S, reduction_ratio=r)
    H, W = 32, 32
    x = tf.random.normal((2, H, W, C))
    out = layer(x)
    
    expected_h = H // S
    expected_w = W // S
    assert out.shape == (2, expected_h, expected_w, C)

def test_serialization():
    layer = Involution(channels=16, kernel_size=3, stride=1)
    config = layer.get_config()
    new_layer = Involution.from_config(config)
    
    x = tf.random.normal((1, 16, 16, 16))
    y1 = layer(x)
    
    # Building the new layer before setting weights
    _ = new_layer(x) 
    new_layer.set_weights(layer.get_weights())
    y2 = new_layer(x)
    
    tf.debugging.assert_near(y1, y2, atol=1e-5)

def test_gradients_exist():
    # Now works with C < default group_channels (16)
    C = 8 
    layer = Involution(channels=C, kernel_size=3)
    x = tf.random.normal((2, 16, 16, C))
    
    with tf.GradientTape() as tape:
        tape.watch(x)
        out = layer(x)
        loss = tf.reduce_mean(out)
    
    grads = tape.gradient(loss, [x] + layer.trainable_variables)
    assert grads[0] is not None
    assert any(g is not None and np.sum(np.abs(g)) > 0 for g in grads[1:])

def test_mixed_precision_compatible():
    try:
        tf.keras.mixed_precision.set_global_policy('mixed_float16')
        layer = Involution(channels=16, kernel_size=3)
        x = tf.random.normal((2, 32, 32, 16))
        out = layer(x)
        assert out.dtype in [tf.float16, tf.float32]
    finally:
        tf.keras.mixed_precision.set_global_policy('float32')

def test_correctness_vs_paper_logic():
    layer = Involution(channels=4, kernel_size=3, stride=1, reduction_ratio=2)
    input_a = tf.random.normal((1, 10, 10, 4))
    input_b = tf.random.normal((1, 10, 10, 4))
    
    _ = layer(input_a) # Build
    for var in layer.trainable_variables:
        var.assign(tf.ones_like(var))
        
    out_a = layer(input_a)
    out_b = layer(input_b)
    assert not np.allclose(out_a.numpy(), out_b.numpy())
