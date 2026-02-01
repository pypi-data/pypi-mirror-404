import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.piratenet import PirateNetBlock

"""
Test suite for PirateNetBlock (TensorFlow)
Paper: Krishnapriyan et al., 'PirateNets: Physics-informed Deep Learning with Residual Adaptive Networks', JMLR 2024.
"""

@pytest.fixture
def input_dim():
    return 32

@pytest.fixture
def batch_size():
    return 8

@pytest.fixture
def model(input_dim):
    return PirateNetBlock(units=input_dim, activation='tanh')

@pytest.fixture
def data(batch_size, input_dim):
    # Keras models usually take a list of inputs or a concatenated tensor
    # Assuming call(inputs) where inputs = [x, U, V]
    x = tf.random.normal((batch_size, input_dim))
    U = tf.random.normal((batch_size, input_dim))
    V = tf.random.normal((batch_size, input_dim))
    return [x, U, V]

def test_instantiation_shape_dtype(model, data):
    """
    Verifies Keras Layer instantiation, shape inference, and dtype conservation.
    """
    x = data[0]
    output = model(data)
    
    assert output.shape == x.shape, f"Expected shape {x.shape}, got {output.shape}"
    assert output.dtype == x.dtype
    assert not np.isnan(output.numpy()).any()

def test_initialization_invariant_identity(model, data):
    """
    CRITICAL PAPER TEST (Section 4, Eq 4.6):
    Verify alpha init to 0 and Identity behavior.
    """
    x = data[0]
    
    # Build the model specifically (if not built automatically)
    _ = model(data)
    
    # Find alpha variable
    alpha_var = None
    for var in model.trainable_variables:
        if 'alpha' in var.name:
            alpha_var = var
            break
    
    assert alpha_var is not None, "Could not find trainable 'alpha' variable"
    np.testing.assert_allclose(alpha_var.numpy(), 0.0, atol=1e-7, 
                               err_msg="Alpha must initialize to 0")

    # Check identity mapping
    output = model(data)
    np.testing.assert_allclose(output.numpy(), x.numpy(), atol=1e-6,
                               err_msg="PirateNet must be identity at init")

def test_gradients_flow(model, data):
    """
    Checks that gradients flow through the block to alpha.
    """
    with tf.GradientTape() as tape:
        output = model(data)
        loss = tf.reduce_mean(tf.square(output))
        
    grads = tape.gradient(loss, model.trainable_variables)
    
    assert len(grads) > 0
    
    # Check specific gradient for alpha
    alpha_grad = None
    for var, grad in zip(model.trainable_variables, grads):
        if 'alpha' in var.name:
            alpha_grad = grad
            
    assert alpha_grad is not None
    assert tf.norm(alpha_grad) > 0.0, "Gradient to alpha is zero"

def test_config_serialization(model):
    """
    Standard Keras test: ensure layer can be serialized/deserialized.
    """
    config = model.get_config()
    new_model = model.__class__.from_config(config)
    assert config['units'] == new_model.get_config()['units']

def test_numerical_stability_large_inputs(model, input_dim, batch_size):
    """
    Test resilience against large inputs (sanity check for internal gating).
    """
    # Large inputs
    x = tf.random.normal((batch_size, input_dim)) * 100.0
    U = tf.random.normal((batch_size, input_dim)) * 100.0
    V = tf.random.normal((batch_size, input_dim)) * 100.0
    
    output = model([x, U, V])
    assert not np.isnan(output.numpy()).any()
