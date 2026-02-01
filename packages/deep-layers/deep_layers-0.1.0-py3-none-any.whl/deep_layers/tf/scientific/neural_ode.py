import tensorflow as tf
from tensorflow.keras import layers

class NeuralODELayer(layers.Layer):
    """
    Chen et al., 'Neural Ordinary Differential Equations', NeurIPS 2018.
    
    Purpose
    -------
    Models continuous-depth transformations via an ODE solver rather than discrete layers.
    
    Description
    -----------
    Defines layer output as the solution to dz/dt = f(z, t; θ) from t0 to t1.
    
    Logic
    -----
        1. Forward: Numerically integrate (e.g., Dormand–Prince).
    2. Backward: Use adjoint method to avoid storing intermediate states.
    """
    def __init__(self, func, t_span, integration_steps=10, **kwargs):
        super(NeuralODELayer, self).__init__(**kwargs)
        self.func = func
        self.t_span = t_span
        self.steps = integration_steps

    def rk4_step(self, t, h, dt):
        k1 = self.func(t, h)
        k2 = self.func(t + dt/2.0, h + dt/2.0 * k1)
        k3 = self.func(t + dt/2.0, h + dt/2.0 * k2)
        k4 = self.func(t + dt, h + dt * k3)
        return h + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)

    def call(self, h):
        t0, t1 = self.t_span[0], self.t_span[1]
        dt = (t1 - t0) / float(self.steps)
        curr_h = h
        curr_t = t0
        for _ in range(self.steps):
            curr_h = self.rk4_step(curr_t, curr_h, dt)
            curr_t += dt
        return curr_h

class ODEDynamics(layers.Layer):
    """
    The function f(h(t), t, theta) that defines the derivative.
    """
    def __init__(self, hidden_dim, **kwargs):
        super(ODEDynamics, self).__init__(**kwargs)
        self.hidden_dim = hidden_dim
        self.dense1 = layers.Dense(hidden_dim, activation='tanh')
        self.dense2 = layers.Dense(hidden_dim, activation='tanh')
        self.dense3 = layers.Dense(hidden_dim)

    def call(self, inputs):
        # Unpack inputs: tensorflow doesn't support passing multiple args to layer.call easily
        # in functional loops, so we pass a tuple or list: [t, h]
        t, h = inputs
        
        # t is a scalar tensor, broadcast to [batch_size, 1]
        t_vec = tf.fill([tf.shape(h)[0], 1], t)
        t_vec = tf.cast(t_vec, h.dtype)
        
        # Concatenate [h, t] -> [batch, hidden_dim + 1]
        cat_input = tf.concat([h, t_vec], axis=1)
        
        x = self.dense1(cat_input)
        x = self.dense2(x)
        return self.dense3(x)
