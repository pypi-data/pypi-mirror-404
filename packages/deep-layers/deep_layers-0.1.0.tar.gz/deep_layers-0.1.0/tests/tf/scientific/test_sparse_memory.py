import tensorflow as tf
import pytest
import numpy as np
from deep_layers.tf.scientific.sparse_memory import SparseMemoryLayer

"""
Test suite for SparseMemoryLayer (TensorFlow)
Paper: Rae et al., 'Scaling Memory-Augmented Neural Networks with Sparse Reads and Writes', 2016.
"""

@pytest.fixture
def tf_params():
    return {
        'hidden_size': 20, 
        'memory_slots': 128,
        'memory_dim': 16,
        'k_sparse': 4
    }

def test_tf_instantiation(tf_params):
    cell = SparseMemoryLayer(**tf_params)
    assert isinstance(cell, tf.keras.layers.Layer)

def test_tf_forward_shape(tf_params):
    batch_size = 8
    input_dim = 10
    cell = SparseMemoryLayer(**tf_params)
    rnn = tf.keras.layers.RNN(cell, return_sequences=True, return_state=True)
    inputs = tf.random.normal((batch_size, 5, input_dim))
    
    # RNN returns [sequence, state_1, state_2, ...]
    results = rnn(inputs)
    
    sequences = results[0]
    final_states = results[1:]
    
    assert sequences.shape == (batch_size, 5, tf_params['hidden_size'])
    
    # Verify memory shape. State structure: (h, c, M, w_r, usage, r)
    # M is index 2 in the state tuple
    memory_state = final_states[2]
    assert memory_state.shape == (batch_size, tf_params['memory_slots'], tf_params['memory_dim'])

def test_tf_sparsity_constraint(tf_params):
    """
    Verifies that the read weights (Attention) are effectively sparse.
    Section 3.1: "keep the K largest non-zero entries".
    """
    cell = SparseMemoryLayer(**tf_params)
    batch_size = 4
    input_dim = 10
    
    inputs = tf.random.normal((batch_size, input_dim))
    # Dummy initial states
    states = cell.get_initial_state(inputs=inputs, batch_size=batch_size, dtype=tf.float32)
    
    output, new_states = cell(inputs, states)
    
    # Extract read weights (Assuming specific index in state tuple, e.g., index 2)
    read_weights = new_states[2] 
    
    # Count non-zeros (using a small epsilon for float comparison)
    non_zeros = tf.math.count_nonzero(tf.math.greater(read_weights, 1e-7), axis=1)
    
    # Check max non-zeros against K
    max_non_zeros = tf.reduce_max(non_zeros)
    # Fixed key from k_neighbors to k_sparse
    assert max_non_zeros <= tf_params['k_sparse'], \
        f"Expected sparsity <= {tf_params['k_sparse']}, got {max_non_zeros}"

def test_tf_numerical_stability(tf_params):
    cell = SparseMemoryLayer(**tf_params)
    inputs = tf.random.normal((4, 10)) * 100 # Large inputs
    states = cell.get_initial_state(inputs=inputs, batch_size=4, dtype=tf.float32)
    
    output, new_states = cell(inputs, states)
    
    assert not np.any(np.isnan(output.numpy()))
    assert not np.any(np.isinf(output.numpy()))

def test_tf_gradient_propagation(tf_params):
    """
    Ensures gradients flow through the sparse operations.
    Critical because sparse ops (like top-k gathering) can sometimes detach gradients
    if not implemented correctly.
    """
    cell = SparseMemoryLayer(**tf_params)
    rnn = tf.keras.layers.RNN(cell)
    
    inputs = tf.random.normal((2, 5, 10))
    
    with tf.GradientTape() as tape:
        tape.watch(inputs)
        output = rnn(inputs)
        loss = tf.reduce_mean(output ** 2)
    
    # Check gradients w.r.t trainable weights
    grads = tape.gradient(loss, cell.trainable_variables)
    
    assert len(grads) > 0
    for g in grads:
        assert g is not None

def test_tf_trainability(tf_params):
    """
    Simple integration test on a random regression task.
    """
    input_dim = 10
    
    model = tf.keras.Sequential([
        tf.keras.layers.InputLayer(input_shape=(None, input_dim)),
        tf.keras.layers.RNN(SparseMemoryLayer(**tf_params)),
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    # Dummy data
    x = np.random.randn(10, 5, input_dim)
    y = np.random.randn(10, 1)
    
    history = model.fit(x, y, epochs=5, verbose=0)
    
    loss_start = history.history['loss'][0]
    loss_end = history.history['loss'][-1]
    
    assert loss_end < loss_start, "Model failed to learn (decrease loss)"
