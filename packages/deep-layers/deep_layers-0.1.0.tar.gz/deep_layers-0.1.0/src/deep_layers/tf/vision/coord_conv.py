import tensorflow as tf
from tensorflow.keras import layers

class CoordConv(tf.keras.layers.Layer):
    """
    Liu et al., 'An Intriguing Failing of Convolutional Neural Networks and the CoordConv Solution', NeurIPS 2018.
    
    Purpose
    -------
    Gives translation-invariant CNNs location awareness (e.g., for Generative/RL tasks).
    
    Description
    -----------
    Concatenates coordinate channels (i, j) to the input feature map before applying convolution.
    
    Logic
    -----
        1. Input: (N, C, H, W).
    2. Generate meshgrid xx (range H) and yy (range W).
    3. Normalize coordinates to [-1, 1].
    4. Concatenate: (N, C+2, H, W).
    5. Apply standard Conv2d.
    """
    def __init__(self, filters, kernel_size, with_r=False, **kwargs):
        super(CoordConv, self).__init__()
        self.add_coords = AddCoords(with_r=with_r)
        self.conv = layers.Conv2D(filters, kernel_size, **kwargs)

    def call(self, inputs):
        ret = self.add_coords(inputs)
        ret = self.conv(ret)
        return ret
class AddCoords(layers.Layer):
    """
    Adds Coordinate channels to the input tensor.
    Input: (batch, x_dim, y_dim, c) [channels_last]
    Output: (batch, x_dim, y_dim, c + 2) or (batch, x_dim, y_dim, c + 3)
    """
    def __init__(self, with_r=False):
        super(AddCoords, self).__init__()
        self.with_r = with_r

    def call(self, input_tensor):
        batch_size_tensor = tf.shape(input_tensor)[0]
        x_dim = tf.shape(input_tensor)[1]
        y_dim = tf.shape(input_tensor)[2]

        # Create coordinate grids
        xx_ones = tf.ones([batch_size_tensor, x_dim], dtype=tf.int32)
        xx_ones = tf.expand_dims(xx_ones, -1)
        
        xx_range = tf.tile(tf.expand_dims(tf.range(y_dim), 0), [batch_size_tensor, 1])
        xx_range = tf.expand_dims(xx_range, 1)
        
        xx_channel = tf.matmul(xx_ones, xx_range)
        xx_channel = tf.expand_dims(xx_channel, -1)
        
        yy_ones = tf.ones([batch_size_tensor, y_dim], dtype=tf.int32)
        yy_ones = tf.expand_dims(yy_ones, 1)
        
        yy_range = tf.tile(tf.expand_dims(tf.range(x_dim), 0), [batch_size_tensor, 1])
        yy_range = tf.expand_dims(yy_range, -1)
        
        yy_channel = tf.matmul(yy_range, yy_ones)
        yy_channel = tf.expand_dims(yy_channel, -1)

        # Normalize to [-1, 1]
        xx_channel = tf.cast(xx_channel, 'float32') / (tf.cast(y_dim, 'float32') - 1)
        yy_channel = tf.cast(yy_channel, 'float32') / (tf.cast(x_dim, 'float32') - 1)
        
        xx_channel = xx_channel * 2 - 1
        yy_channel = yy_channel * 2 - 1

        # Concatenate
        ret = tf.concat([input_tensor, xx_channel, yy_channel], axis=-1)

        # Add Radius channel if requested
        if self.with_r:
            rr = tf.sqrt(tf.square(xx_channel) + tf.square(yy_channel))
            ret = tf.concat([ret, rr], axis=-1)

        return ret
