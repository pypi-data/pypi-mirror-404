import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.sequence.linear_attention import LinearAttentionLayer

"""
Test suite for LinearAttentionLayer (TensorFlow)
Paper: Katharopoulos et al., 'Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention', ICML 2020.
"""

def test_keras_instantiation_shapes():
    """Verifies Keras layer construction and tensor shapes."""
    B, N, D = 2, 64, 32
    layer = LinearAttentionLayer(dim=D, heads=2, causal=False)
    
    x = tf.random.normal((B, N, D))
    out = layer(x, x, x)
    
    assert out.shape == (B, N, D)

def test_keras_serialization():
    """Ensures the layer can be saved/loaded (critical for deployment)."""
    layer = LinearAttentionLayer(dim=32, causal=True)
    config = layer.get_config()
    new_layer = LinearAttentionLayer.from_config(config)
    assert config['causal'] is True

def test_keras_causal_masking():
    """
    Tests Eq 12 (Causal Masking). 
    Position i should only depend on positions j <= i.
    """
    B, N, D = 1, 5, 16
    layer = LinearAttentionLayer(dim=D, causal=True)
    
    x = np.random.randn(B, N, D).astype(np.float32)
    
    # Run twice
    with tf.GradientTape() as tape:
        tape.watch(tf.convert_to_tensor(x))
        out1 = layer(x, x, x)
    
    # Perturb the last token
    x_perturbed = x.copy()
    x_perturbed[:, -1, :] += 10.0
    out2 = layer(x_perturbed, x_perturbed, x_perturbed)
    
    # The first token's output should remain exactly the same
    np.testing.assert_allclose(
        out1.numpy()[:, 0, :], 
        out2.numpy()[:, 0, :], 
        rtol=1e-5, 
        err_msg="Causal mask failure: changing future affected past."
    )

def test_keras_gradients_and_stability():
    """
    Checks if gradients exist and no NaNs are produced 
    via the feature map mechanism (elu+1).
    """
    B, N, D = 2, 20, 32
    layer = LinearAttentionLayer(dim=D, causal=False)
    
    with tf.GradientTape() as tape:
        q = tf.random.normal((B, N, D))
        k = tf.random.normal((B, N, D))
        v = tf.random.normal((B, N, D))
        tape.watch([q, k, v])
        
        out = layer(q, k, v)
        loss = tf.reduce_mean(out)
        
    grads = tape.gradient(loss, [q, k, v])
    
    assert not np.isnan(out.numpy()).any(), "NaNs in forward pass"
    for g in grads:
        assert g is not None, "Gradient connection broken"
        assert not np.isnan(g.numpy()).any(), "NaNs in backward pass"

def test_keras_mixed_precision_compatibility():
    """
    Paper mentions efficiency (Section 2.1). 
    Linear Attention often requires high precision for the cumulative sum, 
    but inputs might be float16.
    """
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    try:
        layer = LinearAttentionLayer(dim=32)
        x = tf.random.normal((2, 10, 32))
        out = layer(x, x, x)
        assert out.dtype == tf.float16
        assert not np.isnan(out.numpy()).any()
    finally:
        # Reset policy
        tf.keras.mixed_precision.set_global_policy('float32')
