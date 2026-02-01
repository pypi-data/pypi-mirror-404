import tensorflow as tf
from tensorflow.keras import layers

"""
Lee et al., 'Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks', ICML 2019.
"""

class MAB(layers.Layer):
    """
    Multihead Attention Block (MAB).
    """
    def __init__(self, d_model, n_heads, d_ff=None, ln=True, **kwargs):
        super(MAB, self).__init__(**kwargs)
        self.d_model = d_model
        self.n_heads = n_heads
        self.ln = ln
        self.d_ff = d_ff if d_ff is not None else d_model

    def build(self, input_shape):
        self.att = layers.MultiHeadAttention(num_heads=self.n_heads, key_dim=self.d_model)
        self.ln0 = layers.LayerNormalization()
        self.ln1 = layers.LayerNormalization()
        
        # Row-wise Feedforward
        self.ff = tf.keras.Sequential([
            layers.Dense(self.d_ff, activation='relu'),
            layers.Dense(self.d_model)
        ])
        super(MAB, self).build(input_shape)

    def call(self, X, Y):
        # Attention: Q=X, K=Y, V=Y
        att_out = self.att(X, Y, Y)
        
        # Residual + Norm
        H = X + att_out
        if self.ln:
            H = self.ln0(H)
            
        # Feed Forward + Residual + Norm
        ff_out = self.ff(H)
        out = H + ff_out
        if self.ln:
            out = self.ln1(out)
            
        return out

class SAB(layers.Layer):
    """
    Set Attention Block (SAB).
    SAB(X) = MAB(X, X)
    """
    def __init__(self, d_model, n_heads, **kwargs):
        super(SAB, self).__init__(**kwargs)
        self.d_model = d_model
        self.n_heads = n_heads
        self.mab = MAB(d_model, n_heads)

    def call(self, X):
        return self.mab(X, X)

class ISAB(layers.Layer):
    """
    Induced Set Attention Block (ISAB).
    Approximation O(nm) complexity.
    """
    def __init__(self, d_model, n_heads, num_inducing, **kwargs):
        super(ISAB, self).__init__(**kwargs)
        self.d_model = d_model
        self.n_heads = n_heads
        self.num_inducing = num_inducing

    def build(self, input_shape):
        # Inducing points I are trainable parameters
        self.I = self.add_weight(
            shape=(1, self.num_inducing, self.d_model),
            initializer="glorot_uniform",
            trainable=True,
            name="inducing_points"
        )
        self.mab0 = MAB(self.d_model, self.n_heads)
        self.mab1 = MAB(self.d_model, self.n_heads)
        super(ISAB, self).build(input_shape)

    def call(self, X):
        batch_size = tf.shape(X)[0]
        # Tile I to match batch size: (Batch, M, Dim)
        I_batch = tf.tile(self.I, [batch_size, 1, 1])
        
        # H = MAB(I, X)
        H = self.mab0(I_batch, X)
        
        # ISAB(X) = MAB(X, H)
        return self.mab1(X, H)

class PMA(layers.Layer):
    """
    Pooling by Multihead Attention (PMA).
    Aggregates set to fixed number of seeds (k).
    """
    def __init__(self, d_model, n_heads, k, **kwargs):
        super(PMA, self).__init__(**kwargs)
        self.d_model = d_model
        self.n_heads = n_heads
        self.k = k

    def build(self, input_shape):
        # Seed vectors S are trainable parameters
        self.S = self.add_weight(
            shape=(1, self.k, self.d_model),
            initializer="glorot_uniform",
            trainable=True,
            name="seed_vectors"
        )
        self.mab = MAB(self.d_model, self.n_heads)
        super(PMA, self).build(input_shape)

    def call(self, X):
        batch_size = tf.shape(X)[0]
        # Tile S to match batch size: (Batch, K, Dim)
        S_batch = tf.tile(self.S, [batch_size, 1, 1])
        
        # PMA(X) = MAB(S, X)
        return self.mab(S_batch, X)
