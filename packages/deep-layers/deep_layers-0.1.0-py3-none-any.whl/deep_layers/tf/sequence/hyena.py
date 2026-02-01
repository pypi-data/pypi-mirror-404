import tensorflow as tf

class HyenaOperator(tf.keras.layers.Layer):
    def __init__(self, d_model, l_max=128, order=2, filter_order=64, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.order = order
        self.l_max = l_max
        self.filter_order = filter_order

    def build(self, input_shape):
        self.in_proj = tf.keras.layers.Dense((self.order + 1) * self.d_model)
        self.short_conv = tf.keras.layers.Conv1D(
            filters=(self.order + 1) * self.d_model,
            kernel_size=3,
            padding='causal', 
            groups=(self.order + 1) * self.d_model 
        )
        self.hyena_filter = HyenaFilter(self.d_model, order=self.order, ffn_dim=self.filter_order)
        self.out_proj = tf.keras.layers.Dense(self.d_model)
        super().build(input_shape)

    def call(self, u):
        B = tf.shape(u)[0]
        L = tf.shape(u)[1]
        D = self.d_model

        projections = self.in_proj(u) 
        projections = self.short_conv(projections)
        projections = tf.reshape(projections, (B, L, self.order + 1, D))
        projections = tf.transpose(projections, perm=[0, 2, 3, 1])
        
        x = projections[:, :-1, :, :] 
        v = projections[:, -1, :, :]  
        
        h = self.hyena_filter(L) 
        
        for n in range(self.order):
            h_n = h[n] 
            x_n = x[:, n] 
            
            padding = [[0, 0], [0, 0], [0, L]] 
            v_padded = tf.pad(v, padding) 
            h_padded = tf.pad(h_n, [[0, 0], [0, L]]) 
            
            v_f = tf.signal.rfft(v_padded)
            h_f = tf.signal.rfft(h_padded)
            y_f = v_f * tf.expand_dims(h_f, 0)
            y = tf.signal.irfft(y_f)
            y = y[..., :L]
            v = y * x_n
            
        v = tf.transpose(v, perm=[0, 2, 1])
        return self.out_proj(v)

    def get_config(self):
        config = super().get_config()
        config.update({
            "d_model": self.d_model,
            "order": self.order,
            "l_max": self.l_max,  # Include l_max in config
            "filter_order": self.filter_order,
        })
        return config

class HyenaFilter(tf.keras.layers.Layer):
    def __init__(self, d_model, emb_dim=33, order=2, ffn_dim=64, freq=10.0, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.emb_dim = emb_dim
        self.order = order
        self.freq = freq
        self.ffn_dim = ffn_dim

    def build(self, input_shape):
        self.dense1 = tf.keras.layers.Dense(self.ffn_dim)
        self.dense2 = tf.keras.layers.Dense(self.order * self.d_model)
        self.bias = self.add_weight(shape=(self.order, self.d_model), initializer="random_normal", name="bias")
        self.decay = self.add_weight(shape=(self.order, self.d_model), initializer="random_normal", name="decay")
        super().build(input_shape)

    def call(self, L):
        L_float = tf.cast(L, tf.float32)
        t = tf.linspace(0.0, 1.0, L)
        t = tf.expand_dims(t, -1) 

        bands = tf.linspace(0.0, tf.cast(self.emb_dim - 1, tf.float32), self.emb_dim)
        bands = tf.reshape(bands, (1, -1))
        z = t * bands * self.freq
        pe = tf.sin(z) 

        h = self.dense1(pe)
        h = tf.sin(self.freq * h) 
        h = self.dense2(h) 
        
        h = tf.reshape(h, (L, self.order, self.d_model))
        h = tf.transpose(h, perm=[1, 2, 0]) 

        t_window = tf.linspace(0.0, L_float, L)
        t_window = tf.reshape(t_window, (1, 1, L))
        
        decay_term = tf.exp(-tf.exp(tf.expand_dims(self.decay, -1)) * t_window)
        bias_term = tf.expand_dims(self.bias, -1)
        
        return h * decay_term + bias_term

    def get_config(self):
        config = super().get_config()
        config.update({
            "d_model": self.d_model,
            "emb_dim": self.emb_dim,
            "order": self.order,
            "ffn_dim": self.ffn_dim,
            "freq": self.freq,
        })
        return config
