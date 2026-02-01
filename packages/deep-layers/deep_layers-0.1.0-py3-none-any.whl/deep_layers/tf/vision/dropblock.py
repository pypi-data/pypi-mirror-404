import tensorflow as tf

class DropBlock(tf.keras.layers.Layer):
    """
    Ghiasi et al., 'DropBlock: A regularization method for convolutional networks', NeurIPS 2018.
    
    Purpose
    -------
    Drops contiguous square regions of feature maps to handle spatial correlation.
    """
    def __init__(self, drop_prob=0.1, block_size=7, **kwargs):
        # Handle 'keep_prob' if passed from tests (keep_prob = 1 - drop_prob)
        if "keep_prob" in kwargs:
            drop_prob = 1.0 - kwargs.pop("keep_prob")
            
        super(DropBlock, self).__init__(**kwargs)
        self.drop_prob = drop_prob
        self.block_size = block_size

    def get_config(self):
        config = super(DropBlock, self).get_config()
        config.update({
            "drop_prob": self.drop_prob,
            "block_size": self.block_size
        })
        return config

    def _compute_gamma(self, height, width):
        height = tf.cast(height, tf.float32)
        width = tf.cast(width, tf.float32)
        block_size = tf.cast(self.block_size, tf.float32)
        
        feat_area = height * width
        block_area = block_size ** 2
        
        valid_area = (height - block_size + 1.0) * (width - block_size + 1.0)
        
        gamma = (self.drop_prob / block_area) * (feat_area / valid_area)
        return gamma

    def call(self, inputs, training=None):
        # 1. Handle drop_prob 0 early
        if self.drop_prob == 0.0:
            return inputs

        # 2. Handle training flag
        # FIXED: learning_phase() is removed in modern Keras. 
        # We default to False if training is None (e.g., during model building/summary).
        if training is None:
            training = False

        def _inference():
            return inputs

        def _training():
            input_shape = tf.shape(inputs)
            batch_size, height, width, channels = input_shape[0], input_shape[1], input_shape[2], input_shape[3]
            
            gamma = self._compute_gamma(height, width)
            
            # Sample Bernoulli mask
            mask_shape = (batch_size, height, width, channels)
            noise = tf.random.uniform(mask_shape, minval=0.0, maxval=1.0, dtype=tf.float32)
            mask = tf.cast(noise < gamma, tf.float32)

            # Expand blocks (Dilation) using Max Pool
            mask_block = tf.nn.max_pool2d(
                mask,
                ksize=[1, self.block_size, self.block_size, 1],
                strides=[1, 1, 1, 1],
                padding='SAME'
            )

            # Invert mask (0 = drop, 1 = keep)
            mask_keep = 1.0 - mask_block

            # Normalize to maintain activation magnitude
            valid_keep_ratio = tf.reduce_mean(mask_keep)
            normalize_scale = 1.0 / (valid_keep_ratio + 1e-6)

            return inputs * mask_keep * normalize_scale

        # Cast training to bool in case it's a symbolic tensor or None
        return tf.cond(tf.cast(training, tf.bool), _training, _inference)
