import tensorflow as tf
from tensorflow.keras import Sequential
import pytest
import numpy as np
from deep_layers.tf.scientific.steerable_conv import SteerableConv

"""
Test suite for SteerableConv (TensorFlow)
Paper: Weiler et al., 'General E(2)-Equivariant Steerable CNNs', NeurIPS 2018.
"""

@pytest.fixture
def layer():
    return SteerableConv(out_channels=8, kernel_size=5)

@pytest.fixture
def input_tensor():
    # Channels Last: (Batch, H, W, Channels)
    return tf.random.normal((2, 32, 32, 3))

def test_instantiation_and_shape(layer, input_tensor):
    """Verifies shape inference and numerical stability."""
    output = layer(input_tensor)
    assert output.shape == (2, 32, 32, 8)
    assert not np.any(np.isnan(output.numpy()))
    assert not np.any(np.isinf(output.numpy()))

def test_gradients(layer, input_tensor):
    """Checks backward pass and gradient connection."""
    with tf.GradientTape() as tape:
        output = layer(input_tensor)
        loss = tf.reduce_mean(output)
    
    grads = tape.gradient(loss, layer.trainable_variables)
    
    assert len(grads) > 0
    for g in grads:
        assert g is not None
        assert tf.norm(g) > 0

def test_model_fitting(layer):
    """Simple overfitting test on random noise."""
    x = tf.random.normal((4, 16, 16, 3))
    y = tf.random.normal((4, 16, 16, 8))
    
    model = Sequential([layer])
    model.compile(optimizer='adam', loss='mse')
    
    history = model.fit(x, y, epochs=50, verbose=0)
    
    # Relaxed assertion: Loss should decrease
    assert history.history['loss'][-1] < history.history['loss'][0]

def test_rotation_equivariance(layer, input_tensor):
    """
    Paper Specific: Rotation Equivariance Check.
    Section 2.3: k(gx) = rho_out(g)k(x)rho_in(g^-1) implies f(gx) = g f(x)
    """
    # 1. Forward Original
    out_original = layer(input_tensor)
    
    # 2. Rotate Input 90 deg (k=1)
    input_rotated = tf.image.rot90(input_tensor, k=1)
    
    # 3. Forward Rotated
    out_from_rotated = layer(input_rotated)
    
    # 4. Transform Original Output (Group action on features)
    # Assuming Trivial Representation (Scalar fields) for simplicity.
    # If output used Regular Representation, we would need to permute channels here.
    out_original_rotated = tf.image.rot90(out_original, k=1)
    
    # 5. Assert Equivariance
    diff = tf.reduce_max(tf.abs(out_from_rotated - out_original_rotated))
    
    # TF rot90 is exact, so tolerance can be tight
    assert diff < 1e-4, f"Equivariance broken. Diff: {diff}"

def test_radial_profile_limit(layer):
    """
    Paper Specific: Bandlimiting / Discretization check.
    The paper mentions Gaussian radial profiles to prevent aliasing.
    Inputting a high-freq "checkerboard" pattern and rotating it shouldn't 
    cause massive variance in activation sum if steerability is preserved.
    """
    x = tf.ones((1, 32, 32, 3))
    # Create a checkerboard (high freq)
    mask = (np.indices((32, 32)).sum(axis=0) % 2).astype(np.float32)
    x = x * mask[..., None]
    
    out_0 = layer(x)
    out_90 = layer(tf.image.rot90(x, k=1))
    
    # The sum of activations (energy) should be conserved under rotation
    energy_0 = tf.reduce_sum(out_0**2)
    energy_90 = tf.reduce_sum(out_90**2)
    
    # Relative error
    rel_err = tf.abs(energy_0 - energy_90) / (energy_0 + 1e-6)
    assert rel_err < 0.05, "Energy conservation violation under rotation (Check aliasing/bandlimits)"
