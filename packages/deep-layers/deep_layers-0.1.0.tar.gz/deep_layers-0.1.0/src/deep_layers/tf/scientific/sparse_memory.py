import tensorflow as tf
from tensorflow.keras import layers

class SparseMemoryLayer(tf.keras.layers.Layer):
    def __init__(self, hidden_size, memory_slots, memory_dim, k_sparse=4, **kwargs):
        super(SparseMemoryLayer, self).__init__(**kwargs)
        self.units = hidden_size # For Keras RNN compatibility
        self.hidden_size = hidden_size
        self.N = memory_slots
        self.W = memory_dim
        self.K = k_sparse
        
        # Controller
        self.controller = layers.LSTMCell(hidden_size)
        
        # Projections
        self.output_projector = layers.Dense(self.W * 3 + 2)
        self.final_projector = layers.Dense(hidden_size)

    @property
    def state_size(self):
        # Keras expects tuples for multi-dim states, not TensorShape objects usually
        return (self.hidden_size, self.hidden_size, 
                (self.N, self.W), 
                (self.N,), 
                (self.N,), 
                self.W)

    def get_initial_state(self, inputs=None, batch_size=None, dtype=None):
        if dtype is None:
            dtype = tf.float32
        
        return (tf.zeros((batch_size, self.hidden_size), dtype=dtype),
                tf.zeros((batch_size, self.hidden_size), dtype=dtype),
                tf.zeros((batch_size, self.N, self.W), dtype=dtype),
                tf.zeros((batch_size, self.N), dtype=dtype),
                tf.zeros((batch_size, self.N), dtype=dtype),
                tf.zeros((batch_size, self.W), dtype=dtype))

    def call(self, inputs, states):
        h_prev, c_prev, M_prev, wr_prev, usage_prev, r_prev = states
        
        # --- 1. Controller ---
        lstm_in = tf.concat([inputs, r_prev], axis=-1)
        h_curr, (h_curr, c_curr) = self.controller(lstm_in, (h_prev, c_prev))
        
        params = self.output_projector(h_curr)
        
        # Split params
        q = params[:, :self.W]
        a = params[:, self.W:2*self.W]
        e = tf.sigmoid(params[:, 2*self.W:3*self.W])
        alpha = tf.sigmoid(params[:, -2:-1])
        gamma = tf.sigmoid(params[:, -1:])
        
        # --- 2. Sparse Read ---
        q_norm = tf.math.l2_normalize(q, axis=1)[:, tf.newaxis, :]
        m_norm = tf.math.l2_normalize(M_prev, axis=2)
        sim = tf.reduce_sum(q_norm * m_norm, axis=2) # [B, N]
        
        top_k_vals, top_k_indices = tf.math.top_k(sim, k=self.K)
        
        batch_size = tf.shape(inputs)[0]
        batch_indices = tf.tile(tf.expand_dims(tf.range(batch_size), 1), [1, self.K])
        
        scatter_indices = tf.stack([
            tf.reshape(batch_indices, [-1]),
            tf.reshape(top_k_indices, [-1])
        ], axis=1)
        
        scatter_updates = tf.reshape(top_k_vals, [-1])
        
        neg_inf = tf.ones([batch_size, self.N]) * -1e9
        logits = tf.tensor_scatter_nd_update(neg_inf, scatter_indices, scatter_updates)
        
        w_r = tf.nn.softmax(logits, axis=1)
        
        r_curr = tf.matmul(tf.expand_dims(w_r, 1), M_prev)
        r_curr = tf.squeeze(r_curr, axis=1)
        
        # --- 3. Write Addressing ---
        usage_curr = usage_prev + 1.0
        access_update = tf.ones_like(scatter_updates)
        access_mask = tf.scatter_nd(scatter_indices, access_update, [batch_size, self.N])
        usage_curr = usage_curr * (1.0 - access_mask)
        
        lru_indices = tf.argmax(usage_curr, axis=1, output_type=tf.int32)
        lru_indices_scatter = tf.stack([tf.range(batch_size), lru_indices], axis=1)
        I_U = tf.scatter_nd(lru_indices_scatter, tf.ones(batch_size), [batch_size, self.N])
        
        w_w = alpha * (gamma * wr_prev + (1.0 - gamma) * I_U)
        
        # --- 4. Memory Update ---
        w_w_exp = tf.expand_dims(w_w, 2)
        e_exp = tf.expand_dims(e, 1)
        a_exp = tf.expand_dims(a, 1)
        
        erase_matrix = w_w_exp * e_exp
        add_matrix = w_w_exp * a_exp
        
        M_curr = M_prev * (1.0 - erase_matrix) + add_matrix
        
        # --- 5. Output ---
        out_vec = tf.concat([h_curr, r_curr], axis=1)
        y_out = self.final_projector(out_vec)
        
        return y_out, (h_curr, c_curr, M_curr, w_r, usage_curr, r_curr)
