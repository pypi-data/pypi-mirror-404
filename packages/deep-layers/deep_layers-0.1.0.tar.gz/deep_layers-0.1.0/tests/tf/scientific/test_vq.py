import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.vq import VQLayer

@pytest.fixture
def vq_params():
    return {'num_embeddings': 512, 'embedding_dim': 64, 'commitment_cost': 0.25}

def test_layer_instantiation_and_shape(vq_params):
    layer = VQLayer(**vq_params)
    x = tf.random.normal((2, 32, 32, 64))
    quantized = layer(x)
    assert quantized.shape == x.shape

def test_output_is_from_codebook(vq_params):
    layer = VQLayer(**vq_params)
    x = tf.random.normal((1, 1, 1, 64))
    quantized = layer(x)
    embeddings = layer.embeddings
    q_vec = tf.reshape(quantized, [-1])
    diffs = tf.reduce_sum(tf.square(embeddings - q_vec), axis=1)
    assert tf.reduce_min(diffs) < 1e-5

def test_straight_through_estimator(vq_params):
    layer = VQLayer(**vq_params)
    x = tf.random.normal((2, 8, 8, 64))
    with tf.GradientTape() as tape:
        tape.watch(x)
        quantized = layer(x)
        loss = tf.reduce_sum(quantized)
    grads = tape.gradient(loss, x)
    assert grads is not None
    assert tf.reduce_sum(tf.abs(grads)) > 0.0

def test_trainability_codebook_update(vq_params):
    layer = VQLayer(**vq_params)
    optimizer = tf.keras.optimizers.Adam(0.1)
    x = tf.random.normal((1, 1, 1, 64))
    q_init = layer(x)
    dist_init = tf.reduce_mean(tf.square(x - q_init))
    
    for _ in range(20):
        with tf.GradientTape() as tape:
            q = layer(x)
            # VQLayer adds its own loss, so we just minimize a dummy or the layer loss
            loss = sum(layer.losses)
        grads = tape.gradient(loss, layer.trainable_variables)
        optimizer.apply_gradients(zip(grads, layer.trainable_variables))
        
    q_final = layer(x)
    dist_final = tf.reduce_mean(tf.square(x - q_final))
    assert dist_final < dist_init

def test_invariants_and_stability(vq_params):
    layer = VQLayer(**vq_params)
    x = tf.random.normal((2, 4, 4, 64)) * 500.0
    quantized = layer(x)
    
    # Check if losses are added
    assert len(layer.losses) > 0
    assert float(sum(layer.losses)) >= 0.0
    
    assert not np.isnan(quantized.numpy()).any()
