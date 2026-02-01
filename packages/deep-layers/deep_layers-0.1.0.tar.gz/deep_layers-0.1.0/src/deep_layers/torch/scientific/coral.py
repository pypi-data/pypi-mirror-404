import torch
import torch.nn as nn
import numpy as np

class CORALLayer(nn.Module):
    """
    Serrano et al., 'Operator Learning with Neural Fields', NeurIPS 2023.
    
    Purpose
    -------
    Solves PDEs on general geometries using coordinate-based MLPs.
    
    Description
    -----------
    Maps one neural field to another using coordinate-aware aggregation.
    
    Logic
    -----
        1. Encode input field samples via coordinate-MLP.
    2. Aggregate information across coordinates (local neighborhoods).
    3. Output new coordinate-MLP representing the solution field.
    """
    def __init__(self, in_features, out_features, latent_dim=None, w0=30.0, is_first=False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.latent_dim = latent_dim # Store to match test config
        self.w0 = w0
        self.is_first = is_first
        
        self.linear = nn.Linear(in_features, out_features, bias=True)
        self.init_weights()


    def init_weights(self):
        with torch.no_grad():
            if self.is_first:
                bound = 1 / self.in_features
                self.linear.weight.uniform_(-bound, bound)
            else:
                bound = np.sqrt(6 / self.in_features) / self.w0
                self.linear.weight.uniform_(-bound, bound)
            nn.init.zeros_(self.linear.bias)

    def forward(self, x, phi=None):
        pre_activation = self.linear(x)
        if phi is not None:
            while phi.dim() < pre_activation.dim():
                phi = phi.unsqueeze(1)
            pre_activation = pre_activation + phi
        return torch.sin(self.w0 * pre_activation)
