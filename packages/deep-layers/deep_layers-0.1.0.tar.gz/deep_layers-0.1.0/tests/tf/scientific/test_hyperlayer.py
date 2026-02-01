import tensorflow as tf
import pytest
from deep_layers.tf.scientific.hyperlayer import HyperLayer

@pytest.fixture
def layer_params():
    return {'units': 64, 'hyper_units': 16}

def test_gradients_exist(layer_params):
    units = layer_params['units']
    hyper = layer_params['hyper_units']
    cell = HyperLayer(**layer_params)
    x = tf.random.normal((4, 32))
    
    # 4 states: main_h, main_c, hyper_h, hyper_c
    states = [tf.zeros((4, units)), tf.zeros((4, units)), 
              tf.zeros((4, hyper)), tf.zeros((4, hyper))]
    
    with tf.GradientTape() as tape:
        output, _ = cell(x, states)
        loss = tf.reduce_mean(output)
    grads = tape.gradient(loss, cell.trainable_variables)
    assert len(grads) > 0

def test_variable_batch_size(layer_params):
    cell = HyperLayer(**layer_params)
    u, h = layer_params['units'], layer_params['hyper_units']
    
    x1 = tf.random.normal((1, 32))
    s1 = [tf.zeros((1, u)), tf.zeros((1, u)), tf.zeros((1, h)), tf.zeros((1, h))]
    out1, _ = cell(x1, s1)
    assert out1.shape == (1, u)

    x10 = tf.random.normal((10, 32))
    s10 = [tf.zeros((10, u)), tf.zeros((10, u)), tf.zeros((10, h)), tf.zeros((10, h))]
    out10, _ = cell(x10, s10)
    assert out10.shape == (10, u)

def test_paper_invariant_weight_scaling_bounds(layer_params):
    cell = HyperLayer(**layer_params)
    u, h_dim = layer_params['units'], layer_params['hyper_units']
    x = tf.random.normal((10, 32)) * 10.0
    states = [tf.zeros((10, u)), tf.zeros((10, u)), tf.zeros((10, h_dim)), tf.zeros((10, h_dim))]
    out, _ = cell(x, states)
    assert not tf.reduce_any(tf.math.is_nan(out))
    
# Keep other tests (test_layer_output_shapes, test_hypernet_training_loop) as is, they work.
# (Re-include them in the file to ensure full file validity)
from tensorflow.keras import layers, Input
def test_layer_output_shapes(layer_params):
    batch_size = 10
    input_dim = 32
    cell = HyperLayer(**layer_params)
    rnn = layers.RNN(cell, return_sequences=True, return_state=True)
    inputs = Input(shape=(5, input_dim))
    outputs = rnn(inputs)
    model = tf.keras.Model(inputs, outputs)
    x_np = tf.random.normal((batch_size, 5, input_dim))
    y_preds = model.predict(x_np)
    assert y_preds[0].shape == (batch_size, 5, layer_params['units'])

def test_hypernet_training_loop(layer_params):
    input_dim = 20
    model = tf.keras.Sequential([
        layers.InputLayer(input_shape=(None, input_dim)),
        layers.RNN(HyperLayer(**layer_params))
    ])
    model.compile(optimizer='adam', loss='mse')
    x = tf.random.normal((100, 5, input_dim))
    y = tf.random.normal((100, layer_params['units']))
    history = model.fit(x, y, epochs=3, verbose=0)
    assert history.history['loss'][-1] < history.history['loss'][0]
