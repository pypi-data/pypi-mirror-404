import tensorflow as tf
import numpy as np

class GCNLayer(tf.keras.layers.Layer):
    """
    Kipf & Welling, 'Semi-Supervised Classification with Graph Convolutional Networks', ICLR 2017.
    """
    def __init__(self, units, use_bias=True, **kwargs):
        super(GCNLayer, self).__init__(**kwargs)
        self.units = units
        self.use_bias = use_bias

    def build(self, input_shape):
        # input_shape will be a list of shapes [features_shape, adj_shape]
        feat_shape = input_shape[0]
        in_features = feat_shape[-1]
        
        self.kernel = self.add_weight(
            shape=(in_features, self.units),
            initializer='glorot_uniform',
            name='kernel'
        )
        if self.use_bias:
            self.bias = self.add_weight(
                shape=(self.units,),
                initializer='zeros',
                name='bias'
            )
        else:
            self.bias = None
        super(GCNLayer, self).build(input_shape)

    def call(self, inputs):
        # inputs: [features, adj]
        # features: (N, in_features)
        # adj: (N, N) - should be normalizedÃ
        features, adj = inputs
        
        # Linear transformation
        # H * W
        support = tf.matmul(features, self.kernel)
        
        # Graph convolution
        # Â * (H * W)
        output = tf.matmul(adj, support)
        
        if self.bias is not None:
            output = output + self.bias
            
        return output

    def get_config(self):
        config = super(GCNLayer, self).get_config()
        config.update({
            'units': self.units,
            'use_bias': self.use_bias
        })
        return config
