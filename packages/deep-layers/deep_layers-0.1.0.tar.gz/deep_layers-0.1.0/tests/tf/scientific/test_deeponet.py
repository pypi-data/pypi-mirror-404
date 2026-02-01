import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.deeponet import DeepONetLayer

"""
Test suite for DeepONetLayer (TensorFlow)
Paper: Lu et al., 'Learning nonlinear operators: The DeepONet architecture', Nature Machine Intelligence 2021.
"""

@pytest.fixture
def keras_dims():
    return {'m': 50, 'd': 2, 'p': 20, 'batch': 32}

@pytest.fixture
def keras_submodels(keras_dims):
    m, d, p = keras_dims['m'], keras_dims['d'], keras_dims['p']
    
    branch = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(p)
    ])
    
    trunk = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(p, activation='tanh')
    ])
    return branch, trunk

@pytest.fixture
def deeponet_model(keras_submodels):
    branch, trunk = keras_submodels
    return DeepONetLayer(branch_net=branch, trunk_net=trunk)

# --- Tests ---

def test_keras_output_shape(deeponet_model, keras_dims):
    """
    Verifies output shape matches (Batch, 1).
    """
    u = tf.random.normal((keras_dims['batch'], keras_dims['m']))
    y = tf.random.normal((keras_dims['batch'], keras_dims['d']))
    
    # Keras inputs are typically a list or tuple
    output = deeponet_model([u, y])
    
    assert output.shape == (keras_dims['batch'], 1)

def test_keras_gradients_exist(deeponet_model, keras_dims):
    """
    Verifies GradientTape can capture gradients for both sub-networks.
    """
    u = tf.random.normal((keras_dims['batch'], keras_dims['m']))
    y = tf.random.normal((keras_dims['batch'], keras_dims['d']))
    
    with tf.GradientTape() as tape:
        output = deeponet_model([u, y])
        loss = tf.reduce_mean(tf.square(output))
        
    grads = tape.gradient(loss, deeponet_model.trainable_variables)
    
    # Ensure we have gradients and they are not all None
    assert len(grads) > 0
    assert not all(g is None for g in grads)
    
    # Specific check: Ensure vars from branch and trunk are included
    branch_vars = deeponet_model.branch_net.trainable_variables
    trunk_vars = deeponet_model.trunk_net.trainable_variables
    assert len(branch_vars) > 0 and len(trunk_vars) > 0

def test_keras_serialization(deeponet_model, keras_dims, tmp_path):
    u = tf.random.normal((10, keras_dims['m']))
    y = tf.random.normal((10, keras_dims['d']))
    
    # Wrap in Model to enable .save()
    inputs_u = tf.keras.Input(shape=(keras_dims['m'],))
    inputs_y = tf.keras.Input(shape=(keras_dims['d'],))
    out = deeponet_model([inputs_u, inputs_y])
    full_model = tf.keras.Model(inputs=[inputs_u, inputs_y], outputs=out)
    
    save_path = tmp_path / "deeponet_saved.keras"
    full_model.save(save_path)
    
    loaded_model = tf.keras.models.load_model(save_path)
    
    # Check consistency
    out_original = deeponet_model([u, y])
    out_loaded = loaded_model([u, y])
    
    tf.debugging.assert_near(out_original, out_loaded)

def test_equation_logic_correctness(keras_dims):
    """
    Validates Eq 2: G(u)(y) = sum(b_k * t_k) + b_0.
    We mock the sub-networks to return fixed values to verify the math.
    """
    m, d, p = keras_dims['m'], keras_dims['d'], 3
    
    # Mock Branch: outputs [1, 2, 3] for every sample
    branch = tf.keras.Sequential([
        tf.keras.layers.Dense(p, kernel_initializer='ones', bias_initializer='zeros'),
        tf.keras.layers.Lambda(lambda x: x * 0 + tf.constant([1., 2., 3.]))
    ])
    
    # Mock Trunk: outputs [4, 5, 6] for every sample
    trunk = tf.keras.Sequential([
        tf.keras.layers.Dense(p, kernel_initializer='ones', bias_initializer='zeros'),
        tf.keras.layers.Lambda(lambda x: x * 0 + tf.constant([4., 5., 6.]))
    ])
    
    model = DeepONetLayer(branch, trunk)
    
    u = tf.zeros((1, m))
    y = tf.zeros((1, d))
    
    # Expected: 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
    # Note: If the implementation includes a bias b0, this might differ slightly,
    # but initially it should be close to dot product.
    
    result = model([u, y])
    assert np.isclose(result.numpy()[0,0], 32.0, atol=1e-5), \
        "The DeepONet combination logic does not equal the dot product of branch and trunk."
