import tensorflow as tf
import numpy as np

class CORALLayer(tf.keras.layers.Layer):
    def __init__(self, units, w0=30.0, is_first=False, **kwargs):
        # Support kwargs for testing flexibility
        kwargs.pop('latent_dim', None)
        kwargs.pop('out_dim', None)
        super().__init__(**kwargs)
        self.units = units
        self.w0 = w0
        self.is_first = is_first
        
    def build(self, input_shape):
        # Handle list input for [coords, latent]
        in_dim = input_shape[0][-1] if isinstance(input_shape, list) else input_shape[-1]
        self.w = self.add_weight(
            shape=(in_dim, self.units),
            initializer=SirenInitializer(self.w0, self.is_first),
            trainable=True,
            name='kernel'
        )
        self.b = self.add_weight(
            shape=(self.units,),
            initializer='zeros',
            trainable=True,
            name='bias'
        )

    def call(self, inputs):
        if isinstance(inputs, list):
            coords, phi = inputs
        else:
            coords, phi = inputs, None

        # Wx + b
        pre_act = tf.matmul(coords, self.w) + self.b
        
        # Apply Shift Modulation: (Wx + b) + phi
        if phi is not None:
            # Broadcast phi (Batch, Units) -> (Batch, 1, Units) to match (Batch, N, Units)
            if len(phi.shape) == 2:
                phi = tf.expand_dims(phi, 1)
            pre_act = pre_act + phi
            
        return tf.math.sin(self.w0 * pre_act)

class SirenInitializer(tf.keras.initializers.Initializer):
    def __init__(self, w0=30.0, is_first=False):
        self.w0 = w0
        self.is_first = is_first
    def __call__(self, shape, dtype=None):
        in_features = shape[0]
        if self.is_first:
            bound = 1 / in_features
        else:
            bound = np.sqrt(6 / in_features) / self.w0
        return tf.random.uniform(shape, -bound, bound, dtype=dtype)
