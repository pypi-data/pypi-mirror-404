import tensorflow as tf
from tensorflow.keras import layers

class Involution(tf.keras.layers.Layer):
    """
    Li et al., 'Involution: Inverting the Inherence of Convolution for Visual Recognition', CVPR 2021.
    """
    def __init__(self, channels, kernel_size=7, stride=1, group_channels=16, reduction_ratio=4, **kwargs):
        super(Involution, self).__init__(**kwargs)
        self.channels = channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.group_channels = group_channels
        self.reduction_ratio = reduction_ratio
        # Ensure groups is at least 1 to avoid filters=0 in Conv2D
        self.groups = max(1, channels // group_channels)
        
    def build(self, input_shape):
        # Kernel Generation Layers
        self.reduce = layers.Conv2D(
            filters=max(1, self.channels // self.reduction_ratio),
            kernel_size=1,
            strides=1,
            padding='same',
            use_bias=False
        )
        self.bn = layers.BatchNormalization()
        self.relu = layers.Activation('relu')
        self.span = layers.Conv2D(
            filters=self.kernel_size * self.kernel_size * self.groups,
            kernel_size=1,
            strides=1,
            padding='same'
        )
        
        if self.stride > 1:
            self.avg_pool = layers.AveragePooling2D(pool_size=self.stride, strides=self.stride)
            
        super(Involution, self).build(input_shape)

    def call(self, inputs):
        x_down = self.avg_pool(inputs) if self.stride > 1 else inputs
        kernel_gen = self.span(self.relu(self.bn(self.reduce(x_down))))
        
        batch_size = tf.shape(kernel_gen)[0]
        h_out = tf.shape(kernel_gen)[1]
        w_out = tf.shape(kernel_gen)[2]
        
        kernel_gen = tf.reshape(
            kernel_gen, 
            (batch_size, h_out, w_out, self.groups, self.kernel_size**2, 1)
        )
        
        patches = tf.image.extract_patches(
            images=inputs,
            sizes=[1, self.kernel_size, self.kernel_size, 1],
            strides=[1, self.stride, self.stride, 1],
            rates=[1, 1, 1, 1],
            padding='SAME'
        )
        
        patches = tf.reshape(
            patches,
            (batch_size, h_out, w_out, self.kernel_size**2, self.groups, self.channels // self.groups)
        )
        
        patches = tf.transpose(patches, perm=[0, 1, 2, 4, 3, 5])
        output = tf.reduce_sum(kernel_gen * patches, axis=4)
        output = tf.reshape(output, (batch_size, h_out, w_out, self.channels))
        
        return output

    def get_config(self):
        config = super().get_config()
        config.update({
            "channels": self.channels,
            "kernel_size": self.kernel_size,
            "stride": self.stride,
            "group_channels": self.group_channels,
            "reduction_ratio": self.reduction_ratio,
        })
        return config
