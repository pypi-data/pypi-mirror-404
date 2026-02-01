import tensorflow as tf

class VQLayer(tf.keras.layers.Layer):
    """
    Van den Oord et al., 'Neural Discrete Representation Learning' (VQ-VAE), NeurIPS 2017.
    
    Purpose
    -------
    Discretizes continuous vectors into the nearest neighbor from a codebook (essential for GenAI).
    
    Description
    -----------
    Maps inputs to the closest embedding in a learnable dictionary using Straight-Through Estimator (STE).
    
    Logic
    -----
        1. Codebook: Learnable weights (NumEmbeddings, Dim).
    2. Distance: Calculate L2 distance between inputs and codebook.
    3. Quantize: Replace input vectors with nearest codebook vectors.
    4. STE: output = input + (quantized - input).detach().
    """
    def __init__(self, num_embeddings, embedding_dim, commitment_cost=0.25, **kwargs):
        super(VQLayer, self).__init__(**kwargs)
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.commitment_cost = commitment_cost

    def build(self, input_shape):
        # Create the embedding codebook variables
        self.embeddings = self.add_weight(
            name='embeddings',
            shape=(self.num_embeddings, self.embedding_dim),
            initializer='uniform',
            trainable=True
        )
        super(VQLayer, self).build(input_shape)

    def call(self, inputs):
        # inputs shape: [Batch, Height, Width, Channel] (Standard TF format)
        
        # Flatten input to [N, Channel]
        input_shape = tf.shape(inputs)
        flat_input = tf.reshape(inputs, [-1, self.embedding_dim])

        # Calculate distances: ||z_e(x) - e_j||^2
        distances = (
            tf.reduce_sum(flat_input**2, axis=1, keepdims=True) +
            tf.reduce_sum(self.embeddings**2, axis=1) -
            2 * tf.matmul(flat_input, self.embeddings, transpose_b=True)
        )

        # Encoding indices: Equation 1 (argmin)
        encoding_indices = tf.argmin(distances, axis=1)
        
        # Quantize: Get the nearest embeddings
        encodings = tf.one_hot(encoding_indices, self.num_embeddings)
        quantized = tf.matmul(encodings, self.embeddings)
        
        # Reshape back to original dimensions [Batch, Height, Width, Channel]
        quantized = tf.reshape(quantized, input_shape)

        # Loss: Equation 3
        # Term 2: Codebook Loss ||sg[z_e(x)] - e||^2
        e_latent_loss = tf.reduce_mean((tf.stop_gradient(inputs) - quantized) ** 2)
        # Term 3: Commitment Loss ||z_e(x) - sg[e]||^2
        q_latent_loss = tf.reduce_mean((inputs - tf.stop_gradient(quantized)) ** 2)
        
        loss = q_latent_loss + self.commitment_cost * e_latent_loss
        
        # Add loss to the layer (Keras will add this to the total training loss automatically)
        self.add_loss(loss)

        # Straight Through Estimator (Equation 2)
        # Copy gradients from quantized to inputs during backprop
        quantized = inputs + tf.stop_gradient(quantized - inputs)

        return quantized
