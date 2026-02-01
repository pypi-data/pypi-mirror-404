import tensorflow as tf
from tensorflow.keras import layers

@tf.keras.utils.register_keras_serializable(package="deep_layers")
class DeepONetLayer(layers.Layer):
    """
    Lu et al., 'Learning nonlinear operators: The DeepONet architecture', Nature Machine Intelligence 2021.
    """
    def __init__(self, branch_net, trunk_net, use_bias=True, **kwargs):
        super(DeepONetLayer, self).__init__(**kwargs)
        self.branch_net = branch_net
        self.trunk_net = trunk_net
        self.use_bias_final = use_bias
        
    def build(self, input_shape):
        if self.use_bias_final:
            self.b0 = self.add_weight(name="b0", shape=(1,), initializer="zeros", trainable=True)
        super().build(input_shape)

    def call(self, inputs):
        u_input, y_input = inputs
        b = self.branch_net(u_input)
        t = self.trunk_net(y_input)
        output = tf.reduce_sum(b * t, axis=1, keepdims=True)
        if self.use_bias_final:
            output += self.b0
        return output

    def get_config(self):
        config = super().get_config()
        config.update({
            "branch_net": tf.keras.utils.serialize_keras_object(self.branch_net),
            "trunk_net": tf.keras.utils.serialize_keras_object(self.trunk_net),
            "use_bias": self.use_bias_final,
        })
        return config

    @classmethod
    def from_config(cls, config):
        branch_net = tf.keras.utils.deserialize_keras_object(config.pop("branch_net"))
        trunk_net = tf.keras.utils.deserialize_keras_object(config.pop("trunk_net"))
        return cls(branch_net=branch_net, trunk_net=trunk_net, **config)
