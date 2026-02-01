import torch
import torch.nn as nn
import torch.fft
import pytest

# ==========================================
# 1. Model Implementation
# ==========================================

class SineActivation(nn.Module):
    def __init__(self, freq=1.0):
        super().__init__()
        self.freq = freq

    def forward(self, x):
        return torch.sin(self.freq * x)

class HyenaFilter(nn.Module):
    """
    Implicitly parameterized long convolution filter.
    Equation 7: h_t = Window(t) * (FFN o PositionalEncoding)(t)
    """
    def __init__(self, d_model, emb_dim=33, order=2, ffn_dim=64, freq=10.0):
        super().__init__()
        self.d_model = d_model
        self.emb_dim = emb_dim
        self.order = order
        self.freq = freq
        
        # Positional Encoding -> MLP -> (Order * d_model)
        self.mlp = nn.Sequential(
            nn.Linear(emb_dim, ffn_dim),
            SineActivation(freq),
            nn.Linear(ffn_dim, order * d_model)
        )
        
        # Initialize MLP weights to be small to prevent exploding filters at start
        for m in self.mlp.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, std=0.02)
                nn.init.zeros_(m.bias)

        # Learnable parameters for the exponential window
        self.bias = nn.Parameter(torch.zeros(order, d_model))
        self.decay = nn.Parameter(torch.ones(order, d_model) * -3.0) 

    def forward(self, L, device):
        # 1. Positional Encoding z_t (using truncated complex exponential basis logic)
        t = torch.linspace(0, 1, L, device=device).unsqueeze(-1) # (L, 1)
        bands = torch.linspace(0.0, self.emb_dim - 1, self.emb_dim, device=device).reshape(1, -1)
        pe = torch.sin(t * bands * self.freq) # (L, emb_dim)
        
        # 2. FFN pass to get raw filters
        h = self.mlp(pe) 
        h = h.view(L, self.order, self.d_model).permute(1, 2, 0) # (Order, d_model, L)
        
        # 3. Apply Window (Exponential Decay)
        # We use t in [0, 1] for the decay to keep it stable regardless of sequence length
        t_window = torch.linspace(0, 1, L, device=device).reshape(1, 1, L)
        decay = torch.exp(-torch.exp(self.decay).unsqueeze(-1) * t_window)
        
        h = h * decay + self.bias.unsqueeze(-1)
        
        # 4. Scaling: Crucial to prevent signal growth during the recurrence
        # The filter is scaled by 1/L or a small constant to keep convolution gain near 1
        return h * (1.0 / L)

class HyenaOperator(nn.Module):
    def __init__(self, d_model, l_max, order=2, filter_order=64):
        super().__init__()
        self.d_model = d_model
        self.order = order
        self.l_max = l_max
        
        self.in_proj = nn.Linear(d_model, (order + 1) * d_model)
        self.short_conv = nn.Conv1d(
            (order + 1) * d_model, (order + 1) * d_model, 
            kernel_size=3, padding=1, groups=(order + 1) * d_model
        )
        self.hyena_filter = HyenaFilter(d_model, order=order, ffn_dim=filter_order)
        self.out_proj = nn.Linear(d_model, d_model)
        
    def forward(self, u):
        B, L, D = u.shape
        
        # 1. Projections and Short Conv
        res = self.in_proj(u).transpose(1, 2) # (B, (N+1)*D, L)
        res = self.short_conv(res)
        
        # Split into x_n gating branches and v value branch
        res = res.view(B, self.order + 1, D, L)
        x = res[:, :-1] 
        v = res[:, -1]  
        
        # 2. Generate Filters
        h = self.hyena_filter(L, u.device)
        
        # 3. Hyena Recurrence (Algorithm 3)
        for n in range(self.order):
            h_n = h[n]     # (D, L)
            x_n = x[:, n]  # (B, D, L)
            
            # FFT Convolution (Linear convolution via padding to 2L)
            v_fft = torch.fft.rfft(v, n=2*L)
            h_fft = torch.fft.rfft(h_n, n=2*L)
            
            y = torch.fft.irfft(v_fft * h_fft, n=2*L)[..., :L]
            v = y * x_n
            
        return self.out_proj(v.transpose(1, 2))