import tensorflow as tf
from tensorflow.keras import layers

class PhyCRNetLayer(layers.Layer):
    """
    Fan et al., 'Physics-informed convolutional-recurrent neural networks for solving PDEs', CMAME 2022.
    
    Purpose
    -------
    Solves spatiotemporal PDEs by encoding physical constraints into the ConvRNN cell.
    
    Description
    -----------
    A ConvRNN where the hidden state update respects physical discretization schemes.
    
    Logic
    -----
    1. Convolutional encoder for spatial features.
    2. Recurrent update rule mimics PDE time-stepping (e.g., u_t+1 = u_t + Δt · Model(u_t)).
    3. Enforce boundary conditions explicitly.
    """
    def __init__(self, filters, kernel_size, periodic_padding=True, **kwargs):
        """
        Args:
            filters: Output dimensionality (hidden state channels).
            kernel_size: Integer or tuple/list of 2 integers.
            periodic_padding: Boolean. If True, applies circular padding.
        """
        super(PhyCRNetLayer, self).__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        self.periodic_padding = periodic_padding
        
        # We use 'valid' padding in the conv layer because we handle padding manually
        self.conv = layers.Conv2D(
            filters=4 * filters,
            kernel_size=kernel_size,
            padding='valid', 
            use_bias=True
        )

    def build(self, input_shape):
        super(PhyCRNetLayer, self).build(input_shape)

    def _periodic_pad(self, x, kernel_size):
        """
        Implements Periodic (Circular) Padding for TensorFlow
        """
        pad_h = kernel_size // 2
        pad_w = kernel_size // 2
        
        # Pad Top/Bottom (wrapping around)
        top_pad = x[:, -pad_h:, :, :]
        bottom_pad = x[:, :pad_h, :, :]
        x = tf.concat([top_pad, x, bottom_pad], axis=1)
        
        # Pad Left/Right (wrapping around)
        left_pad = x[:, :, -pad_w:, :]
        right_pad = x[:, :, :pad_w, :]
        x = tf.concat([left_pad, x, right_pad], axis=2)
        
        return x

    def call(self, inputs, states):
        """
        Args:
            inputs: Input tensor (Batch, H, W, Channels)
            states: List containing [h_cur, c_cur]
        """
        h_cur, c_cur = states
        
        # Eq (2): Concatenate input and hidden state
        # TF usually works with Channels Last
        combined = tf.concat([inputs, h_cur], axis=-1)

        # Apply Padding
        if self.periodic_padding:
            combined_padded = self._periodic_pad(combined, self.kernel_size)
        else:
            # Fallback to standard zero padding (SAME equivalent via padding layer)
            p = self.kernel_size // 2
            combined_padded = tf.pad(combined, [[0,0], [p,p], [p,p], [0,0]])

        # Convolution
        combined_conv = self.conv(combined_padded)

        # Split into gates
        # Order: i, f, c_tilde, o
        cc_i, cc_f, cc_c, cc_o = tf.split(combined_conv, num_or_size_splits=4, axis=-1)

        # Eq (2) Activations
        i = tf.math.sigmoid(cc_i)
        f = tf.math.sigmoid(cc_f)
        o = tf.math.sigmoid(cc_o)
        g = tf.math.tanh(cc_c) # C_tilde

        # Eq (2) Updates
        c_next = f * c_cur + i * g
        h_next = o * tf.math.tanh(c_next)

        return h_next, [h_next, c_next]
