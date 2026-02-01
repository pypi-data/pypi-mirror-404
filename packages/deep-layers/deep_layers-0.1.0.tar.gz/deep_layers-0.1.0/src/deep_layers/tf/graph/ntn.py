import tensorflow as tf
from tensorflow.keras import layers, initializers, activations

class NTNLayer(tf.keras.layers.Layer):
    """
    Socher et al., 'Reasoning With Neural Tensor Networks for Knowledge Base Completion', NeurIPS 2013.
    
    Purpose
    -------
    Relational reasoning using a bilinear tensor product.
    
    Description
    -----------
    Computes bilinear tensor products between two entity vectors.
    
    Logic
    -----
        1. For vectors e1, e2 and relation R.
    2. Compute e1^T W_R^{[k]} e2 for k slices of tensor W_R.
    3. Concatenate with linear transformation and apply activation.
    """
    def __init__(self, output_dim, input_dim, activation='tanh', **kwargs):
        """
        Args:
            output_dim (k): The number of slices in the tensor (k in the paper).
            input_dim (d): The dimension of the entity vectors.
            activation: Activation function f (default is tanh as per paper).
        """
        super(NTNLayer, self).__init__(**kwargs)
        self.output_dim = output_dim  # k
        self.input_dim = input_dim    # d
        self.activation = activations.get(activation)

    def build(self, input_shape):
        # The Tensor W: shape (d, d, k)
        self.W = self.add_weight(
            name="W_tensor",
            shape=(self.input_dim, self.input_dim, self.output_dim),
            initializer=initializers.GlorotUniform(),
            trainable=True
        )

        # The Standard Matrix V: shape (k, 2d) 
        # Note: In Keras Dense, weights are (input, output), so (2d, k)
        self.V = self.add_weight(
            name="V_matrix",
            shape=(2 * self.input_dim, self.output_dim),
            initializer=initializers.GlorotUniform(),
            trainable=True
        )

        # The Bias b: shape (k,)
        self.b = self.add_weight(
            name="b_bias",
            shape=(self.output_dim,),
            initializer=initializers.Zeros(),
            trainable=True
        )

        # The Output Vector u: shape (k, 1)
        self.u = self.add_weight(
            name="u_vector",
            shape=(self.output_dim, 1),
            initializer=initializers.GlorotUniform(),
            trainable=True
        )
        
        super(NTNLayer, self).build(input_shape)

    def call(self, inputs):
        """
        Args:
            inputs: A list or tuple containing [entity_1, entity_2]
                    Each has shape (batch_size, input_dim)
        """
        e1, e2 = inputs

        # 1. Bilinear Tensor Product: e1^T * W * e2
        # Equation: batch(b), dim(i), dim(j), slices(k)
        # We compute sum(e1_bi * W_ijk * e2_bj) -> result_bk
        tensor_product = tf.einsum('bi,ijk,bj->bk', e1, self.W, e2)

        # 2. Standard Feed Forward: V * [e1, e2]
        concatenated = tf.concat([e1, e2], axis=1) # Shape (batch, 2d)
        standard_product = tf.matmul(concatenated, self.V) # Shape (batch, k)

        # 3. Combine + Bias: (Tensor + Standard + b)
        hidden_layer = tensor_product + standard_product + self.b

        # 4. Nonlinearity: f(...)
        activated_hidden = self.activation(hidden_layer)

        # 5. Final Score: u^T * hidden
        # Shape (batch, 1)
        score = tf.matmul(activated_hidden, self.u)

        return score
