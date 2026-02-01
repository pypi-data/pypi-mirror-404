import tensorflow as tf
from tensorflow.keras import layers

class LinearAttentionLayer(tf.keras.layers.Layer):
    def __init__(self, dim, heads=8, dim_head=None, dropout=0.0, causal=False, **kwargs):
        super(LinearAttentionLayer, self).__init__(**kwargs)
        self.dim = dim
        self.heads = heads
        # Default dim_head based on input dim if not provided
        self.dim_head = dim_head if dim_head is not None else dim // heads
        self.inner_dim = self.heads * self.dim_head
        self.dropout_rate = dropout
        self.causal = causal
        
    def build(self, input_shape):
        self.to_qkv = layers.Dense(self.inner_dim * 3, use_bias=False)
        self.to_out = tf.keras.Sequential([
            layers.Dense(self.dim),
            layers.Dropout(self.dropout_rate)
        ])
        super().build(input_shape)

    def feature_map(self, x):
        return tf.nn.elu(x) + 1.0

    def call(self, q, k=None, v=None, mask=None, causal=None):
        is_causal = causal if causal is not None else self.causal
        b_shape = tf.shape(q)
        b, n = b_shape[0], b_shape[1]
        
        if k is None or v is None:
            qkv = self.to_qkv(q)
            qkv = tf.reshape(qkv, (b, n, 3, self.heads, self.dim_head))
            qkv = tf.transpose(qkv, (2, 0, 3, 1, 4))
            q, k, v = qkv[0], qkv[1], qkv[2]
        else:
            def prepare(t):
                # Only reshape/transpose if it's still in (B, L, D) format
                if len(t.shape) == 3 or tf.rank(t) == 3:
                    d_h = tf.shape(t)[-1] // self.heads
                    t = tf.reshape(t, (b, tf.shape(t)[1], self.heads, d_h))
                    return tf.transpose(t, (0, 2, 1, 3))
                return t
            q, k, v = prepare(q), prepare(k), prepare(v)

        q = self.feature_map(q)
        k = self.feature_map(k)

        if mask is not None:
            mask_float = tf.cast(mask[:, None, :, None], dtype=q.dtype)
            k = k * mask_float
            v = v * mask_float

        if is_causal:
            k_v = tf.einsum('bhnd,bhne->bhnde', k, v)
            context = tf.cumsum(k_v, axis=2)
            k_cumsum = tf.cumsum(k, axis=2)
            numerator = tf.einsum('bhnd,bhnde->bhne', q, context)
            denominator = tf.einsum('bhnd,bhnd->bhn', q, k_cumsum)
            denominator = tf.expand_dims(denominator, -1) + 1e-6
            out = numerator / denominator
        else:
            kv = tf.einsum('bhnd,bhne->bhde', k, v)
            numerator = tf.einsum('bhnd,bhde->bhne', q, kv)
            k_sum = tf.reduce_sum(k, axis=2)
            denominator = tf.einsum('bhnd,bhd->bhn', q, k_sum)
            denominator = tf.expand_dims(denominator, -1) + 1e-6
            out = numerator / denominator

        out = tf.transpose(out, (0, 2, 1, 3))
        out = tf.reshape(out, (b, n, self.inner_dim))
        return self.to_out(out)

    def get_config(self):
        config = super().get_config()
        config.update({
            "dim": self.dim,
            "heads": self.heads,
            "dim_head": self.dim_head,
            "dropout": self.dropout_rate,
            "causal": self.causal
        })
        return config
