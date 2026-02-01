import torch
import torch.nn as nn
import torch.nn.functional as F

class GLU(nn.Module):
    """
    Dauphin et al., 'Language Modeling with Gated Convolutional Networks', ICML 2017.
    
    Purpose
    -------
    A gating mechanism for sequences or grids, often replacing ReLU to control information flow.
    
    Description
    -----------
    Splits the input into two parts, passes one through a sigmoid gate, and multiplies it by the other.
    
    Logic
    -----
    1. Split input channels into A and B.
    2. Output Y = A ⊙ σ(B).
    """
    def __init__(self, in_channels, out_channels, kernel_size, dilation=1):
        super(GLU, self).__init__()
        
        self.kernel_size = kernel_size
        self.dilation = dilation
        
        # Calculate padding size required for causal convolution
        # (k - 1) * dilation
        self.padding = (kernel_size - 1) * dilation
        
        # The paper utilizes weight normalization, which helps convergence.
        # We project to 2 * out_channels to compute both the linear (W) 
        # and gating (V) components simultaneously.
        self.conv = torch.nn.utils.weight_norm(
            nn.Conv1d(
                in_channels, 
                out_channels * 2, 
                kernel_size, 
                dilation=dilation,
                bias=True
            )
        )

    def forward(self, x):
        # x shape: (Batch, Channels, Time)
        
        # 1. Causal Padding
        # We pad only the left side (past) of the time dimension.
        # F.pad argument format for 1D: (padding_left, padding_right)
        x_padded = F.pad(x, (self.padding, 0))
        
        # 2. Convolution
        # Output shape: (Batch, out_channels * 2, Time)
        conv_out = self.conv(x_padded)
        
        # 3. Gating (GLU)
        # Split the output channel-wise into Linear (P) and Gating (Q) components
        # P = X * W + b
        # Q = X * V + c
        P, Q = conv_out.chunk(2, dim=1)
        
        # Equation: P * Sigmoid(Q)
        return P * torch.sigmoid(Q)
