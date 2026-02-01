import tensorflow as tf
from tensorflow.keras import layers

class MambaBlock(tf.keras.layers.Layer):
    """
    Gu & Dao, 'Mamba: Linear-Time Sequence Modeling with Selective State Spaces', arXiv:2312.00752.
    
    Purpose
    -------
    Selective state-space models with input-dependent parameters for long-context modeling.
    
    Description
    -----------
    Discretizes continuous SSM parameters (A, B, Δ) based on input.
    
    Logic
    -----
        1. Project input to Δ, B, C.
    2. Discretize A and B using Δ.
    3. Selective Scan operation (cumulative sum).
    """
    def __init__(self, d_model, d_state=16, d_conv=4, expand=2, **kwargs):
        """
        TensorFlow implementation of the Mamba Block.
        """
        super().__init__(**kwargs)
        self.d_model = d_model
        self.d_state = d_state
        self.d_conv = d_conv
        self.expand = expand
        self.d_inner = int(self.expand * self.d_model)
        self.dt_rank = self.d_inner // 16

    def build(self, input_shape):
        # 1. Input Projection
        self.in_proj = layers.Dense(self.d_inner * 2, use_bias=False)

        # 2. Convolution (1D)
        # Depthwise Conv1D in TF is usually done via SeparableConv or specific settings
        self.conv1d = layers.Conv1D(
            filters=self.d_inner,
            kernel_size=self.d_conv,
            groups=self.d_inner,
            padding='causal',
            use_bias=True
        )

        # 4. SSM Parameters
        self.x_proj = layers.Dense(self.dt_rank + self.d_state * 2, use_bias=False)
        self.dt_proj = layers.Dense(self.d_inner, use_bias=True)

        # A Parameter (log scale) - initialized as S4D-Real
        # Shape (D_inner, N)
        A_init = tf.range(1, self.d_state + 1, dtype=tf.float32)
        A_init = tf.repeat(A_init[tf.newaxis, :], self.d_inner, axis=0)
        self.A_log = self.add_weight(
            name="A_log",
            shape=(self.d_inner, self.d_state),
            initializer=tf.constant_initializer(tf.math.log(A_init).numpy()),
            trainable=True
        )

        # D Parameter
        self.D = self.add_weight(
            name="D",
            shape=(self.d_inner,),
            initializer='ones',
            trainable=True
        )

        # 5. Output Projection
        self.out_proj = layers.Dense(self.d_model, use_bias=False)
        
        super().build(input_shape)

    def call(self, x):
        batch_size = tf.shape(x)[0]
        seq_len = tf.shape(x)[1]

        # 1. Input Projections
        xz = self.in_proj(x)
        x_inner, z = tf.split(xz, num_or_size_splits=2, axis=-1)

        # 2. Conv1D
        x_inner = self.conv1d(x_inner)
        
        # 3. Activation
        x_inner = tf.nn.silu(x_inner)

        # 4. Selective Scan
        y = self.selective_scan(x_inner, batch_size)

        # 5. Gating
        y = y * tf.nn.silu(z)

        # 6. Output Projection
        return self.out_proj(y)

    def selective_scan(self, u, batch_size):
        """
        Performs the selective scan using tf.scan for the recurrence.
        """
        # Projections to generate parameters
        x_dbl = self.x_proj(u) # (B, L, dt_rank + 2N)
        
        dt_low, B, C = tf.split(
            x_dbl, 
            [self.dt_rank, self.d_state, self.d_state], 
            axis=-1
        )
        
        dt = tf.nn.softplus(self.dt_proj(dt_low)) # (B, L, D)

        # Discretize A
        # A is (D, N)
        A = -tf.exp(self.A_log)
        
        # dA = exp(dt * A)
        # einsum: dt (B, L, D), A (D, N) -> (B, L, D, N)
        dA = tf.exp(tf.einsum("bld,dn->bldn", dt, A))
        
        # dB = dt * B
        # einsum: dt (B, L, D), B (B, L, N) -> (B, L, D, N)
        dB = tf.einsum("bld,bln->bldn", dt, B)

        # Prepare for tf.scan
        # Transpose to (L, B, ...) to iterate over time
        u_t = tf.transpose(u, [1, 0, 2])       # (L, B, D)
        dA_t = tf.transpose(dA, [1, 0, 2, 3])  # (L, B, D, N)
        dB_t = tf.transpose(dB, [1, 0, 2, 3])  # (L, B, D, N)
        C_t = tf.transpose(C, [1, 0, 2])       # (L, B, N)

        # Initial state h: (B, D, N)
        h0 = tf.zeros((batch_size, self.d_inner, self.d_state))

        # Scan function
        # state: h (B, D, N)
        # elems: (dA_t, dB_t, u_t)
        def scan_fn(h_prev, elems):
            a_step, b_step, u_step = elems
            # h_t = A_bar * h_{t-1} + B_bar * x_t
            # u_step is (B, D) -> (B, D, 1)
            return a_step * h_prev + b_step * tf.expand_dims(u_step, -1)

        # Run recurrence
        # Returns stacked h over time: (L, B, D, N)
        h_all = tf.scan(scan_fn, (dA_t, dB_t, u_t), initializer=h0)

        # Compute output y
        # h_all: (L, B, D, N)
        # C_t: (L, B, N)
        # D: (D)
        
        # y = C * h + D * u
        # einsum: h (L, B, D, N), C (L, B, N) -> (L, B, D)
        y = tf.einsum("lbdn,lbn->lbd", h_all, C_t)
        
        # Add residual D connection
        y = y + u_t * self.D
        
        # Transpose back to (B, L, D)
        y = tf.transpose(y, [1, 0, 2])
        
        return y
