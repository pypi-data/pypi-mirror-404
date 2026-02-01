import tensorflow as tf
import pytest
from deep_layers.tf.scientific.neural_ode import NeuralODELayer

"""
Test suite for NeuralODELayer (TensorFlow)
Paper: Chen et al., 'Neural Ordinary Differential Equations', NeurIPS 2018.
"""

class SimpleDynamics(tf.keras.Model):
    def __init__(self, units):
        super().__init__()
        self.dense = tf.keras.layers.Dense(units, activation='tanh')

    def call(self, t, x):
        # TensorFlow ODE solvers often expect signature call(t, x)
        return self.dense(x)

@pytest.fixture
def input_tensor():
    return tf.random.normal((32, 10), dtype=tf.float32)

@pytest.fixture
def dynamics_model():
    return SimpleDynamics(units=10)

def test_layer_instantiation_and_shape(input_tensor, dynamics_model):
    """Verifies Keras Layer contract and shape preservation."""
    t_span = tf.constant([0.0, 1.0])
    layer = NeuralODELayer(dynamics_model, t_span)
    
    output = layer(input_tensor)
    
    # Input (B, D) -> Output (B, D) (assuming final state return)
    assert output.shape == input_tensor.shape
    assert output.dtype == input_tensor.dtype

def test_numerical_stability_tf(input_tensor, dynamics_model):
    """Checks for NaNs/Infs during graph execution."""
    t_span = tf.constant([0.0, 5.0])
    layer = NeuralODELayer(dynamics_model, t_span)
    
    output = layer(input_tensor)
    assert tf.reduce_all(tf.math.is_finite(output))

def test_gradient_tape_compatibility(input_tensor, dynamics_model):
    t_span = tf.constant([0.0, 1.0])
    layer = NeuralODELayer(dynamics_model, t_span)
    
    with tf.GradientTape(persistent=True) as tape: # Add persistent=True
        tape.watch(input_tensor)
        output = layer(input_tensor)
        loss = tf.reduce_sum(output)
        
    grads = tape.gradient(loss, dynamics_model.trainable_variables)
    input_grads = tape.gradient(loss, input_tensor)
    
    assert len(grads) > 0
    assert input_grads is not None

def test_trainability_one_step(dynamics_model):
    """Simple training step to ensure connectivity in the computation graph."""
    x = tf.random.normal((10, 10))
    y = x * 2.0 # Target transformation
    
    t_span = tf.constant([0.0, 1.0])
    layer = NeuralODELayer(dynamics_model, t_span)
    optimizer = tf.keras.optimizers.Adam(0.01)
    
    initial_loss = float("inf")
    
    with tf.GradientTape() as tape:
        pred = layer(x)
        loss = tf.reduce_mean(tf.square(pred - y))
        initial_loss = loss
        
    grads = tape.gradient(loss, dynamics_model.trainable_variables)
    optimizer.apply_gradients(zip(grads, dynamics_model.trainable_variables))
    
    # Check updated loss
    pred_new = layer(x)
    loss_new = tf.reduce_mean(tf.square(pred_new - y))
    
    assert loss_new < initial_loss

def test_zero_time_interval(input_tensor, dynamics_model):
    r"""
    Edge Case: Integrating from t -> t should result in Identity.
    h(t) + \int_t^t f(z) = h(t).
    """
    t_span = tf.constant([0.0, 0.0]) # Zero duration
    layer = NeuralODELayer(dynamics_model, t_span)
    
    output = layer(input_tensor)
    
    # Should be exactly equal (or extremely close due to float precision)
    tf.debugging.assert_near(input_tensor, output, atol=1e-6)
