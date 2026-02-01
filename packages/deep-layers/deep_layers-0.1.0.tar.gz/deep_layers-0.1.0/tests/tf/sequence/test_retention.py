import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.sequence.retention import RetentionLayer

"""
Test suite for RetentionLayer (TensorFlow)
Paper: Sun et al., 'Retentive Network: A Successor to Transformer for Large Language Models', ICLR 2024.
"""

BATCH_SIZE = 2
SEQ_LEN = 8
D_MODEL = 64
N_HEADS = 4

@pytest.fixture
def layer():
    return RetentionLayer(embed_dim=D_MODEL, num_heads=N_HEADS)

def test_shape_and_initialization(layer):
    x = tf.random.normal((BATCH_SIZE, SEQ_LEN, D_MODEL))
    y = layer(x)
    assert y.shape == (BATCH_SIZE, SEQ_LEN, D_MODEL)
    assert len(layer.trainable_weights) > 0

def test_chunkwise_recurrent_concept(layer):
    x = tf.random.normal((BATCH_SIZE, SEQ_LEN * 2, D_MODEL))
    full_out = layer(x)

    chunk_1 = x[:, :SEQ_LEN, :]
    chunk_2 = x[:, SEQ_LEN:, :]

    # Call first chunk (starts at 0)
    out_1, state_1 = layer(chunk_1, return_state=True, use_recurrent=True, start_index=0)
    # Call second chunk (starts at SEQ_LEN)
    out_2, _ = layer(chunk_2, initial_state=state_1, use_recurrent=True, return_state=True, start_index=SEQ_LEN)

    concatenated = tf.concat([out_1, out_2], axis=1)
    
    np.testing.assert_allclose(full_out.numpy(), concatenated.numpy(), atol=1e-4, 
                            err_msg="Chunkwise recurrence mismatch")

def test_gradients_exist(layer):
    x = tf.random.normal((BATCH_SIZE, SEQ_LEN, D_MODEL))
    with tf.GradientTape() as tape:
        y = layer(x)
        loss = tf.reduce_mean(y**2)
    
    grads = tape.gradient(loss, layer.trainable_weights)
    assert all(g is not None for g in grads)
    assert not any(np.isnan(g).any() for g in grads)

def test_masking_support(layer):
    """
    RetNet is autoregressive. Ensure Keras Masking is handled or 
    implicit causal masking is applied.
    """
    x = tf.random.normal((BATCH_SIZE, SEQ_LEN, D_MODEL))
    
    # Create a mask where the last timestep is masked out
    mask = np.ones((BATCH_SIZE, SEQ_LEN), dtype=bool)
    mask[:, -1] = False
    mask_tensor = tf.constant(mask)
    
    # Pass with mask
    out_masked = layer(x, mask=mask_tensor)
    
    # In a properly implemented causal layer, masking the last token 
    # shouldn't change the output of previous tokens compared to unmasked run
    # (assuming the layer handles the mask argument)
    out_unmasked = layer(x)
    
    # Check t=0 to t=SEQ_LEN-2 are identical
    np.testing.assert_allclose(
        out_masked[:, :-1, :].numpy(), 
        out_unmasked[:, :-1, :].numpy(), 
        atol=1e-5
    )
