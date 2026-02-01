import tensorflow as tf
from tensorflow.keras import layers # Missing import fixed

class GLU(tf.keras.layers.Layer):
    """
    Dauphin et al., 'Language Modeling with Gated Convolutional Networks', ICML 2017.
    
    Purpose
    -------
    A gating mechanism for sequences or grids, often replacing ReLU to control information flow.
    
    Description
    -----------
    Splits the input into two parts, passes one through a sigmoid gate, and multiplies it by the other.
    
    Logic
    -----
        1. Split input channels into A and B.
    2. Output Y = A ⊙ σ(B).
    """
    def __init__(self, filters, kernel_size, dilation_rate=1, **kwargs):
        super(GLU, self).__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        self.dilation_rate = dilation_rate
        
        # We initialize the convolution with 2 * filters.
        # The output will be split to serve as the content and the gate.
        self.conv = layers.Conv1D(
            filters=filters * 2,
            kernel_size=kernel_size,
            dilation_rate=dilation_rate,
            padding='causal',  # Automatically handles the (k-1) left-padding
            use_bias=True
        )

    def call(self, inputs):
        # inputs shape: (Batch, Time, Channels)
        
        # 1. Causal Convolution
        # Output shape: (Batch, Time, filters * 2)
        conv_out = self.conv(inputs)
        
        # 2. Gating (GLU)
        # Split the last dimension (channels) into two halves
        # a = X * W + b
        # b = X * V + c
        a, b = tf.split(conv_out, 2, axis=-1)
        
        # Equation: a * Sigmoid(b)
        return a * tf.nn.sigmoid(b)
