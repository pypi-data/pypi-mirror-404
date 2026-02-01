import tensorflow as tf
from tensorflow.keras import layers

class PirateNetBlock(layers.Layer):
    """
    Krishnapriyan et al., 'PirateNets: Physics-informed Deep Learning with Residual Adaptive Networks', JMLR 2024.
    
    Purpose
    -------
    Improves PINN training stability via adaptive residual connections.
    
    Description
    -----------
    Starts shallow, progressively deepens during training; initialization tailored for PDE residuals.
    
    Logic
    -----
        1. Define a block with potential sub-blocks.
    2. Schedule the activation of sub-blocks during training.
    3. Initialize specifically to minimize derivative discontinuity.
    """

    def __init__(self, units, activation='tanh', **kwargs):
        super(PirateNetBlock, self).__init__(**kwargs)
        self.units = units
        self.activation = tf.keras.activations.get(activation)
        
        # Dense layers corresponding to Equations 4.1, 4.3, and 4.5
        # Weights initialized via Glorot, Biases to zero (as per Section 4)
        self.dense_f = layers.Dense(units, kernel_initializer='glorot_normal', bias_initializer='zeros')
        self.dense_g = layers.Dense(units, kernel_initializer='glorot_normal', bias_initializer='zeros')
        self.dense_h = layers.Dense(units, kernel_initializer='glorot_normal', bias_initializer='zeros')

    def build(self, input_shape):
        # Learnable parameter alpha, initialized to 0 (Eq 4.6 and paragraph below it)
        # This ensures the block is an identity mapping at initialization.
        self.alpha = self.add_weight(
            name="alpha",
            shape=(),
            initializer="zeros",
            trainable=True
        )
        super(PirateNetBlock, self).build(input_shape)

    def call(self, inputs):
        # Unpack inputs: The layer input x, and the global gates U and V
        # Note: U and V are computed once from the embedding and passed to every block
        x_l, U, V = inputs

        # Eq 4.1: f = sigma(W1 * x + b1)
        f = self.activation(self.dense_f(x_l))

        # Eq 4.2: z1 = f . U + (1 - f) . V (Gating operation)
        z1 = f * U + (1.0 - f) * V

        # Eq 4.3: g = sigma(W2 * z1 + b2)
        g = self.activation(self.dense_g(z1))

        # Eq 4.4: z2 = g . U + (1 - g) . V (Gating operation)
        z2 = g * U + (1.0 - g) * V

        # Eq 4.5: h = sigma(W3 * z2 + b3)
        h = self.activation(self.dense_h(z2))

        # Eq 4.6: x_next = alpha * h + (1 - alpha) * x
        # Adaptive residual connection
        x_next = self.alpha * h + (1.0 - self.alpha) * x_l

        return x_next

class PirateNet(tf.keras.Model):
    """
    Full PirateNet assembly including Random Fourier Features and Gating.
    """
    def __init__(self, output_dim, hidden_dim=256, num_blocks=3, fourier_sigma=1.0, input_dim=2, **kwargs):
        super(PirateNet, self).__init__(**kwargs)
        self.hidden_dim = hidden_dim
        self.fourier_sigma = fourier_sigma
        
        # Random Fourier Feature Matrix B (fixed, not trainable)
        # Assuming input dimension is known or handled dynamically
        self.B = tf.Variable(
            initial_value=tf.random.normal((input_dim, hidden_dim // 2), stddev=fourier_sigma),
            trainable=False,
            dtype=tf.float32,
            name='fourier_B'
        )

        # Layers to generate Gates U and V
        self.gate_U = layers.Dense(hidden_dim, activation='tanh', kernel_initializer='glorot_normal')
        self.gate_V = layers.Dense(hidden_dim, activation='tanh', kernel_initializer='glorot_normal')

        # Stack of PirateNet Blocks
        self.blocks = [PirateNetBlock(hidden_dim, activation='tanh') for _ in range(num_blocks)]
        
        # Final output layer (Eq 4.7 / 4.8)
        self.final_layer = layers.Dense(output_dim, kernel_initializer='glorot_normal')

    def call(self, inputs):
        # 1. Coordinate Embedding (Phi)
        # Input x: (batch, input_dim) -> (batch, hidden_dim/2)
        projected = tf.matmul(inputs, self.B)
        # Phi: (batch, hidden_dim) via [cos, sin]
        phi = tf.concat([tf.cos(projected), tf.sin(projected)], axis=-1)

        # 2. Compute Global Gates U and V
        U = self.gate_U(phi)
        V = self.gate_V(phi)

        # 3. Pass through residual blocks
        x = phi # Initial input to blocks is the embedding
        for block in self.blocks:
            x = block([x, U, V])

        # 4. Final output
        return self.final_layer(x)
