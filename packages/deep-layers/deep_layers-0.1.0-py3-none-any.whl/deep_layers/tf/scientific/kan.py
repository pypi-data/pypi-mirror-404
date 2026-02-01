import tensorflow as tf

class KANLayer(tf.keras.layers.Layer):
    """
    Liu et al., 'KAN: Kolmogorov-Arnold Networks', arXiv:2404.19756 (April 2024).
    """
    def __init__(
        self,
        in_features,
        out_features,
        grid_size=5,
        spline_order=3,
        scale_noise=0.1,
        scale_base=1.0,
        scale_spline=1.0,
        enable_standalone_scale_spline=True,
        base_activation="silu",
        grid_range=[-1, 1],
        **kwargs
    ):
        super(KANLayer, self).__init__(**kwargs)
        self.in_features = in_features
        self.out_features = out_features
        self.grid_size = grid_size
        self.spline_order = spline_order
        self.scale_noise = scale_noise
        self.scale_base = scale_base
        self.scale_spline = scale_spline
        self.enable_standalone_scale_spline = enable_standalone_scale_spline
        self.base_activation = tf.keras.activations.get(base_activation)
        self.grid_range = grid_range

    def build(self, input_shape):
        # Use layer's dtype policy to determine grid precision
        dtype = self.dtype or tf.keras.backend.floatx()
        
        # Create grid with correct dtype
        h = (self.grid_range[1] - self.grid_range[0]) / self.grid_size
        grid_points = (
            tf.range(-self.spline_order, self.grid_size + self.spline_order + 1, dtype=dtype) 
            * tf.cast(h, dtype) + tf.cast(self.grid_range[0], dtype)
        )
        # (in_features, grid_size + 2 * spline_order + 1)
        self.grid = tf.tile(tf.expand_dims(grid_points, 0), [self.in_features, 1])
        
        # Parameters
        self.base_weight = self.add_weight(
            name="base_weight",
            shape=(self.out_features, self.in_features),
            initializer=tf.keras.initializers.VarianceScaling(scale=self.scale_base, mode='fan_in', distribution='uniform'),
            trainable=True
        )
        
        self.spline_weight = self.add_weight(
            name="spline_weight",
            shape=(self.out_features, self.in_features, self.grid_size + self.spline_order),
            initializer=tf.keras.initializers.RandomUniform(minval=-self.scale_noise, maxval=self.scale_noise),
            trainable=True
        )

        if self.enable_standalone_scale_spline:
            self.spline_scaler = self.add_weight(
                name="spline_scaler",
                shape=(self.out_features, self.in_features),
                initializer=tf.keras.initializers.Constant(self.scale_spline),
                trainable=True
            )

        super(KANLayer, self).build(input_shape)

    def b_splines(self, x):
        """
        Compute B-spline bases.
        x: (batch, in_features)
        """
        # Expand dims for broadcasting
        x_expanded = tf.expand_dims(x, -1) # (batch, in, 1)
        grid_expanded = tf.expand_dims(self.grid, 0) # (1, in, grid_len)
        
        # Order 0
        bases = tf.cast(
            tf.logical_and(
                x_expanded >= grid_expanded[:, :, :-1],
                x_expanded < grid_expanded[:, :, 1:]
            ),
            dtype=self.dtype
        )
        
        # Recursion for higher orders
        for k in range(1, self.spline_order + 1):
            t = grid_expanded[:, :, :-(k+1)]
            val = (x_expanded - t) / (grid_expanded[:, :, k:-1] - t) * bases[:, :, :-1]
            
            t = grid_expanded[:, :, k+1:]
            val += (t - x_expanded) / (t - grid_expanded[:, :, 1:-k]) * bases[:, :, 1:]
            bases = val
            
        return bases

    def call(self, x):
        # 1. Base activation path
        base_output = tf.matmul(self.base_activation(x), self.base_weight, transpose_b=True)
        
        # 2. Spline path
        spline_basis = self.b_splines(x) # (batch, in, num_coeffs)
        
        # Compute sum_i (c_i * B_i(x)) using einsum
        spline_output = tf.einsum('bic,oic->bo', spline_basis, self.spline_weight)
        
        if self.enable_standalone_scale_spline:
            weighted_spline_weight = self.spline_weight * tf.expand_dims(self.spline_scaler, -1)
            spline_output = tf.einsum('bic,oic->bo', spline_basis, weighted_spline_weight)

        return base_output + spline_output
