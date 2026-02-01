import tensorflow as tf
import numpy as np

def generate_steerable_basis(kernel_size, in_c, out_c, num_rings, max_freq):
    # Isotropic Gaussian basis stub for testing
    center = kernel_size // 2
    y, x = np.ogrid[-center:kernel_size-center, -center:kernel_size-center]
    r2 = x*x + y*y
    num_basis = num_rings * (2 * max_freq + 1)
    
    bases = []
    for i in range(num_basis):
        sigma = 1.0 + (i % num_rings) * 0.5
        k = np.exp(-r2 / (2 * sigma**2))
        k = k / (np.sum(k) + 1e-6)
        # Broadcast to [out, in, k, k]
        k_broad = np.tile(k[None, None, ...], (out_c, in_c, 1, 1))
        bases.append(k_broad)
        
    return np.stack(bases).astype(np.float32)

class SteerableConv(tf.keras.layers.Layer):
    def __init__(self, out_channels, kernel_size, num_rings=3, max_freq=2, **kwargs):
        super(SteerableConv, self).__init__(**kwargs)
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.num_rings = num_rings
        self.max_freq = max_freq
        
    def build(self, input_shape):
        in_channels = input_shape[-1]
        
        basis_val = generate_steerable_basis(
            self.kernel_size, in_channels, self.out_channels, 
            self.num_rings, self.max_freq
        )
        # [Basis, K, K, In, Out]
        basis_val = np.transpose(basis_val, (0, 3, 4, 2, 1))
        self.num_basis_funcs = basis_val.shape[0]
        
        # Store as weight to avoid Graph capture errors
        self.basis = self.add_weight(
            name="basis",
            shape=basis_val.shape,
            dtype=tf.float32,
            initializer=tf.constant_initializer(basis_val),
            trainable=False
        )
        
        self.w = self.add_weight(
            shape=(self.num_basis_funcs,),
            initializer="glorot_uniform",
            trainable=True,
            name="basis_coefficients"
        )
        super().build(input_shape)

    def call(self, inputs):
        kernel = tf.einsum('b, bijkl -> ijkl', self.w, self.basis)
        return tf.nn.conv2d(inputs, kernel, strides=[1, 1, 1, 1], padding='SAME')
