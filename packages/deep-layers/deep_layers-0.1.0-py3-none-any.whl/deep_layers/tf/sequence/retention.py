import tensorflow as tf
from tensorflow.keras import layers

class RetentionLayer(layers.Layer):
    def __init__(self, embed_dim, num_heads, gate_activation='swish', **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scaling = self.head_dim ** -0.5
        self.gate_activation_name = gate_activation
        self.gate_activation = tf.keras.activations.get(gate_activation)

    def build(self, input_shape):
        self.q_proj = layers.Dense(self.embed_dim, use_bias=False)
        self.k_proj = layers.Dense(self.embed_dim, use_bias=False)
        self.v_proj = layers.Dense(self.embed_dim, use_bias=False)
        self.g_proj = layers.Dense(self.embed_dim, use_bias=False)
        self.out_proj = layers.Dense(self.embed_dim, use_bias=False)
        
        # GroupNorm will be applied token-wise via reshape in call()
        self.group_norm = layers.GroupNormalization(groups=self.num_heads, axis=-1)
        
        idx = tf.range(0, self.num_heads, dtype=tf.float32)
        self.gammas = 1.0 - 2.0 ** (-5.0 - idx)
        super().build(input_shape)

    def get_rotary_embedding(self, seq_len, start_index=0):
        indices = tf.range(0, self.head_dim, 2, dtype=tf.float32)
        inv_freq = 1.0 / (10000.0 ** (indices / self.head_dim))
        t = tf.range(start_index, start_index + seq_len, dtype=tf.float32)
        freqs = tf.einsum('i,j->ij', t, inv_freq)
        emb = tf.concat((freqs, freqs), axis=-1)
        return tf.cos(emb), tf.sin(emb)

    def rotate_tensor(self, x, cos, sin):
        d = tf.shape(x)[-1]
        x1 = x[..., :d//2]
        x2 = x[..., d//2:]
        rotated = tf.concat([-x2, x1], axis=-1)
        return (x * cos) + (rotated * sin)

    def call(self, inputs, mask=None, return_state=False, initial_state=None, use_recurrent=False, start_index=0):
        B = tf.shape(inputs)[0]
        L = tf.shape(inputs)[1]
        
        q = self.q_proj(inputs)
        k = self.k_proj(inputs)
        v = self.v_proj(inputs)
        
        q = tf.transpose(tf.reshape(q, (B, L, self.num_heads, self.head_dim)), perm=[0, 2, 1, 3])
        k = tf.transpose(tf.reshape(k, (B, L, self.num_heads, self.head_dim)), perm=[0, 2, 1, 3])
        v = tf.transpose(tf.reshape(v, (B, L, self.num_heads, self.head_dim)), perm=[0, 2, 1, 3])
        
        cos, sin = self.get_rotary_embedding(L, start_index=start_index)
        cos = tf.reshape(cos, (1, 1, L, self.head_dim))
        sin = tf.reshape(sin, (1, 1, L, self.head_dim))
        q = self.rotate_tensor(q, cos, sin)
        k = self.rotate_tensor(k, cos, sin)

        if use_recurrent:
            state = initial_state if initial_state is not None else tf.zeros((B, self.num_heads, self.head_dim, self.head_dim))
            outputs = []
            decay = tf.reshape(self.gammas, (1, self.num_heads, 1, 1))
            for t in range(L):
                q_t = q[:, :, t:t+1, :]
                k_t = k[:, :, t:t+1, :]
                v_t = v[:, :, t:t+1, :]
                state = state * decay + tf.matmul(k_t, v_t, transpose_a=True)
                out_t = tf.matmul(q_t, state) * self.scaling
                outputs.append(out_t)
            output = tf.concat(outputs, axis=2)
            current_state = state
        else:
            retention = tf.matmul(q, k, transpose_b=True) * self.scaling
            n_idx = tf.reshape(tf.range(L, dtype=tf.float32), (L, 1))
            m_idx = tf.reshape(tf.range(L, dtype=tf.float32), (1, L))
            diff = n_idx - m_idx
            causal_mask = tf.linalg.band_part(tf.ones((L, L)), -1, 0)
            decay_rates = tf.reshape(self.gammas, (self.num_heads, 1, 1))
            decay_matrix = (decay_rates ** diff) * causal_mask
            retention = retention * decay_matrix
            output = tf.matmul(retention, v)
            current_state = None

        output = tf.transpose(output, perm=[0, 2, 1, 3])
        output = tf.reshape(output, (B, L, self.embed_dim))
        
        # Apply GroupNorm token-wise to maintain consistency between 
        # parallel and recurrent modes across different sequence lengths.
        # Reshaping to treating each (Batch * Length) as an independent example.
        output_flat = tf.reshape(output, (-1, self.embed_dim))
        output_flat = self.group_norm(output_flat)
        output = tf.reshape(output_flat, (B, L, self.embed_dim))
        
        gate = self.gate_activation(self.g_proj(inputs))
        output = gate * output
        output = self.out_proj(output)
        
        if return_state:
            return output, current_state
        return output

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "gate_activation": self.gate_activation_name,
        })
        return config
