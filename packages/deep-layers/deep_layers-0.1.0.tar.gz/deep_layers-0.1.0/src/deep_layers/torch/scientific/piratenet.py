import torch
import torch.nn as nn

class PirateNetLayer(nn.Module):
    """
    Krishnapriyan et al., 'PirateNets: Physics-informed Deep Learning with Residual Adaptive Networks', JMLR 2024.
    
    Purpose
    -------
    Improves PINN training stability via adaptive residual connections.
    
    Description
    -----------
    Starts shallow, progressively deepens during training; initialization tailored for PDE residuals.
    
    Logic
    -----
        1. Define a block with potential sub-blocks.
    2. Schedule the activation of sub-blocks during training.
    3. Initialize specifically to minimize derivative discontinuity.
    """
    """
    Full PirateNet assembly including Random Fourier Features and Gating.
    """
    def __init__(self, input_dim, output_dim, hidden_dim=256, num_blocks=3, fourier_sigma=1.0):
        super(PirateNetLayer, self).__init__()
        self.hidden_dim = hidden_dim
        
        # Random Fourier Feature Matrix B (Buffer means it's part of state_dict but not a parameter)
        # B shape: (hidden_dim // 2, input_dim) to result in hidden_dim features after cos/sin concat
        self.register_buffer('B', torch.randn(hidden_dim // 2, input_dim) * fourier_sigma)

        # Layers to generate Gates U and V
        self.gate_U = nn.Linear(hidden_dim, hidden_dim)
        self.gate_V = nn.Linear(hidden_dim, hidden_dim)
        
        # Activation for gates (Paper uses same activation usually)
        self.activation = nn.Tanh()

        # Stack of PirateNet Blocks
        self.blocks = nn.ModuleList([
            PirateNetBlock(hidden_dim, activation='tanh') for _ in range(num_blocks)
        ])
        
        # Final output layer
        self.final_layer = nn.Linear(hidden_dim, output_dim)
        
        # Init gate/final layers
        nn.init.xavier_normal_(self.gate_U.weight)
        nn.init.zeros_(self.gate_U.bias)
        nn.init.xavier_normal_(self.gate_V.weight)
        nn.init.zeros_(self.gate_V.bias)
        nn.init.xavier_normal_(self.final_layer.weight)
        nn.init.zeros_(self.final_layer.bias)

    def forward(self, x):
        # 1. Coordinate Embedding (Phi)
        # x: (batch, input_dim), B: (hidden/2, input_dim)
        # projected: (batch, hidden/2)
        projected = x @ self.B.T
        phi = torch.cat([torch.cos(projected), torch.sin(projected)], dim=-1)

        # 2. Compute Global Gates U and V
        U = self.activation(self.gate_U(phi))
        V = self.activation(self.gate_V(phi))

        # 3. Pass through residual blocks
        out = phi
        for block in self.blocks:
            out = block(out, U, V)

        # 4. Final output
        return self.final_layer(out)
class PirateNetBlock(nn.Module):
    """
    Implements the PirateNet Residual Block described in Equations 4.1 - 4.6.
    """
    def __init__(self, units, activation='tanh'):
        super(PirateNetBlock, self).__init__()
        
        # Activation function
        if activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'swish':
            self.activation = nn.SiLU() # Swish
        else:
            self.activation = nn.Tanh()

        # Dense layers corresponding to Equations 4.1, 4.3, and 4.5
        self.dense_f = nn.Linear(units, units)
        self.dense_g = nn.Linear(units, units)
        self.dense_h = nn.Linear(units, units)
        
        # Initialize weights (Glorot) and biases (Zeros)
        self._init_weights()

        # Learnable parameter alpha, initialized to 0 (Eq 4.6)
        self.alpha = nn.Parameter(torch.zeros(1), requires_grad=True)

    def _init_weights(self):
        for m in [self.dense_f, self.dense_g, self.dense_h]:
            nn.init.xavier_normal_(m.weight)
            nn.init.zeros_(m.bias)

    def forward(self, x_l, U, V):
        # Eq 4.1: f = sigma(W1 * x + b1)
        f = self.activation(self.dense_f(x_l))

        # Eq 4.2: z1 = f . U + (1 - f) . V (Gating operation)
        # Element-wise multiplication
        z1 = f * U + (1.0 - f) * V

        # Eq 4.3: g = sigma(W2 * z1 + b2)
        g = self.activation(self.dense_g(z1))

        # Eq 4.4: z2 = g . U + (1 - g) . V
        z2 = g * U + (1.0 - g) * V

        # Eq 4.5: h = sigma(W3 * z2 + b3)
        h = self.activation(self.dense_h(z2))

        # Eq 4.6: x_next = alpha * h + (1 - alpha) * x
        x_next = self.alpha * h + (1.0 - self.alpha) * x_l

        return x_next
