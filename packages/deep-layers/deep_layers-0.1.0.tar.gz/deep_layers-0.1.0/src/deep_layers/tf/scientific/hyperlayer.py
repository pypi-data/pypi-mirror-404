import tensorflow as tf
from tensorflow.keras import layers

class HyperLayer(tf.keras.layers.Layer):
    """
    Ha et al., 'HyperNetworks', 2016.
    
    Purpose
    -------
    Dynamically generates weights for a main layer based on a context vector.
    
    Description
    -----------
    A small 'hypernetwork' outputs the weights of a larger layer.
    
    Logic
    -----
        1. Input context z.
    2. HyperNetwork H_θ(z) outputs weight matrix W and bias b.
    3. Main layer computes y = Wx + b.
    """
    def __init__(self, units, hyper_units, **kwargs):
        super(HyperLayer, self).__init__(**kwargs)
        self.units = units
        self.hyper_units = hyper_units
        
        # State size is a tuple: (main_h, main_c, hyper_h, hyper_c)
        self._state_size = [self.units, self.units, self.hyper_units, self.hyper_units]

    @property
    def state_size(self):
        return self._state_size

    def build(self, input_shape):
        input_dim = input_shape[-1]
        
        # --- Main LSTM Static Weights ---
        # 4 * units for input, forget, cell, output gates
        self.kernel = self.add_weight(
            shape=(input_dim, 4 * self.units),
            initializer='glorot_uniform',
            name='main_kernel'
        )
        self.recurrent_kernel = self.add_weight(
            shape=(self.units, 4 * self.units),
            initializer='orthogonal',
            name='main_recurrent_kernel'
        )
        self.bias = self.add_weight(
            shape=(4 * self.units,),
            initializer='zeros',
            name='main_bias'
        )
        
        # Layer Normalization
        self.layer_norm = layers.LayerNormalization(center=False, scale=False)
        self.cell_norm = layers.LayerNormalization(center=False, scale=False)

        # --- HyperNetwork Components ---
        # Hyper LSTM Cell
        self.hyper_cell = layers.LSTMCell(self.hyper_units)
        
        # Projection layers to generate scaling vectors (d)
        # We need to project hyper_output -> 4*units scaling vector for x contribution
        # and hyper_output -> 4*units scaling vector for h contribution
        self.z_to_dx = layers.Dense(4 * self.units, name='z_to_dx')
        self.z_to_dh = layers.Dense(4 * self.units, name='z_to_dh')
        self.z_to_db = layers.Dense(4 * self.units, name='z_to_db')
        
        self.built = True

    def call(self, inputs, states):
        # Unpack states
        main_h, main_c, hyper_h, hyper_c = states
        
        # --- 1. Update HyperNetwork ---
        # Input to HyperNet is concatenation of x_t and h_{t-1} (Eq 6)
        hyper_input = tf.concat([inputs, main_h], axis=-1)
        
        # Run standard LSTM Cell for the HyperNetwork
        # LSTMCell expects a list of states [h, c]
        hyper_out, [hyper_h_new, hyper_c_new] = self.hyper_cell(
            hyper_input, [hyper_h, hyper_c]
        )
        
        # --- 2. Generate Scaling Vectors ---
        d_x = self.z_to_dx(hyper_out)
        d_h = self.z_to_dh(hyper_out)
        d_b = self.z_to_db(hyper_out)
        
        # --- 3. Compute Main LSTM (Equation 12) ---
        # Static projections
        proj_x = tf.matmul(inputs, self.kernel) + self.bias
        proj_h = tf.matmul(main_h, self.recurrent_kernel)
        
        # Apply dynamic scaling (element-wise multiplication)
        gates = (d_x * proj_x) + (d_h * proj_h) + d_b
        
        # Apply Layer Normalization
        gates = self.layer_norm(gates)
        
        # Split gates
        i, f, g, o = tf.split(gates, 4, axis=-1)
        
        # Apply activations
        in_gate = tf.sigmoid(i)
        forget_gate = tf.sigmoid(f)
        cell_gate = tf.tanh(g)
        out_gate = tf.sigmoid(o)
        
        # Update Main Cell State
        main_c_new = (forget_gate * main_c) + (in_gate * cell_gate)
        
        # Update Main Hidden State
        # Paper recommends LN on cell state before output gate interaction
        normalized_c = self.cell_norm(main_c_new)
        main_h_new = out_gate * tf.tanh(normalized_c)
        
        return main_h_new, [main_h_new, main_c_new, hyper_h_new, hyper_c_new]
