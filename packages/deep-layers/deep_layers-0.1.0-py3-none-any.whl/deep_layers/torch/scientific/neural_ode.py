import torch
import torch.nn as nn

class NeuralODELayer(nn.Module):
    def __init__(self, hidden_dim_or_func=None, t_range=[0.0, 1.0], integration_steps=10, hidden_dim=None):
        super(NeuralODELayer, self).__init__()
        # Use hidden_dim if provided as kwarg, else use positional arg
        dim = hidden_dim if hidden_dim is not None else hidden_dim_or_func
        if isinstance(dim, nn.Module):
            self.func = dim
        else:
            self.func = ODEDynamics(dim)
        self.steps = int(integration_steps)
        self.t_start = float(t_range[0])
        self.t_end = float(t_range[1])

    def rk4_step(self, func, t, h, dt):
        k1 = func(t, h)
        k2 = func(t + dt/2, h + dt/2 * k1)
        k3 = func(t + dt/2, h + dt/2 * k2)
        k4 = func(t + dt, h + dt * k3)
        return h + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)

    def forward(self, h):
        dt = (self.t_end - self.t_start) / self.steps
        t = self.t_start
        for _ in range(self.steps):
            h = self.rk4_step(self.func, t, h, dt)
            t += dt
        return h

class ODEDynamics(nn.Module):
    def __init__(self, hidden_dim):
        super(ODEDynamics, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim + 1, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim)
        )

    def forward(self, t, h):
        t_vec = torch.ones(h.shape[0], 1, device=h.device) * t
        cat_input = torch.cat([h, t_vec], dim=1)
        return self.net(cat_input)
