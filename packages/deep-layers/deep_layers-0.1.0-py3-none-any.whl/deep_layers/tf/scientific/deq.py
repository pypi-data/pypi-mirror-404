import tensorflow as tf

@tf.keras.utils.register_keras_serializable(package="deep_layers")
class DEQLayer(tf.keras.layers.Layer):
    def __init__(self, f_layer, max_iter=50, tol=1e-3, **kwargs):
        super(DEQLayer, self).__init__(**kwargs)
        self.f = f_layer 
        self.max_iter = max_iter
        self.tol = tol

    def call(self, x):
        @tf.custom_gradient
        def deq_solve(x_in):
            # Forward Pass
            z = tf.zeros_like(x_in)
            # Run fixed iterations to be graph-friendly
            for _ in range(self.max_iter):
                z = self.f([z, x_in])
            
            z_star = tf.stop_gradient(z)

            def backward(grad_output, variables=None):
                # Backward Pass: Solve adjoint
                y = grad_output
                for _ in range(self.max_iter):
                    with tf.GradientTape() as tape:
                        tape.watch(z_star)
                        z_next = self.f([z_star, x_in])
                    
                    # Vector-Jacobian Product
                    vjp = tape.gradient(z_next, z_star, output_gradients=y)
                    y = grad_output + vjp
                
                # Gradients w.r.t input and weights
                with tf.GradientTape() as tape:
                    tape.watch(x_in)
                    # Use the passed variables if available, else layer variables
                    train_vars = variables if variables is not None else self.f.trainable_variables
                    tape.watch(train_vars)
                    z_final = self.f([z_star, x_in])
                
                # Compute gradients for input and variables
                grads = tape.gradient(z_final, [x_in] + train_vars, output_gradients=y)
                return grads[0], grads[1:]

            return z_star, backward

        return deq_solve(x)

    def get_config(self):
        config = super().get_config()
        config.update({
            "f_layer": tf.keras.utils.serialize_keras_object(self.f),
            "max_iter": self.max_iter,
            "tol": self.tol
        })
        return config

    @classmethod
    def from_config(cls, config):
        f_layer = tf.keras.utils.deserialize_keras_object(config.pop("f_layer"))
        return cls(f_layer=f_layer, **config)
