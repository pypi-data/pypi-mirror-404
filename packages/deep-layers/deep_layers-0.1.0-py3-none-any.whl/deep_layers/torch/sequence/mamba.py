import torch
import torch.nn as nn
import torch.nn.functional as F
class MambaBlock(nn.Module):
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
    def __init__(self, d_model, d_state=16, d_conv=4, expand=2):
        """
        MambaBlock from the paper 'Mamba: Linear-Time Sequence Modeling with Selective State Spaces'
        
        Args:
            d_model: Input dimension.
            d_state: SSM state dimension (N in paper).
            d_conv: Convolutional kernel size.
            expand: Expansion factor for the inner dimension (E in paper).
        """
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        self.d_conv = d_conv
        self.expand = expand
        self.d_inner = int(self.expand * self.d_model)
        self.dt_rank = self.d_inner // 16 # Parameterization of Delta

        # 1. Input Projection
        self.in_proj = nn.Linear(d_model, self.d_inner * 2, bias=False)

        # 2. Convolution (1D)
        self.conv1d = nn.Conv1d(
            in_channels=self.d_inner,
            out_channels=self.d_inner,
            bias=True,
            kernel_size=d_conv,
            groups=self.d_inner,
            padding=d_conv - 1,
        )

        # 3. Activation
        self.activation = nn.SiLU()

        # 4. SSM Parameters
        # Projection for input-dependent selection (x -> dt, B, C)
        # B and C have shape (Batch, Length, d_state)
        # dt has shape (Batch, Length, d_inner) via low-rank projection
        self.x_proj = nn.Linear(self.d_inner, self.dt_rank + self.d_state * 2, bias=False)
        
        # dt projection 
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner, bias=True)

        # S4D real initialization for A (diagonal)
        
        A = torch.arange(1, self.d_state + 1, dtype=torch.float32)
        A = A.unsqueeze(0).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A)) # Keep A positive in log space
        self.D = nn.Parameter(torch.ones(self.d_inner)) # Skip connection

        # 5. Output Projection
        self.out_proj = nn.Linear(self.d_inner, d_model, bias=False)

    def forward(self, x):
        """
        Args:
            x: shape (Batch, Seq_Len, Dim)
        """
        batch_size, seq_len, _ = x.shape

        # 1. Input Projection: (B, L, D) -> (B, L, 2*D_inner)
        xz = self.in_proj(x)
        x, z = xz.chunk(2, dim=-1)

        # 2. Conv1D processing
        # Rearrange to (B, D_inner, L) for Conv1d
        x = x.transpose(1, 2)
        x = self.conv1d(x)[:, :, :seq_len] # Causal convolution, remove padding
        x = x.transpose(1, 2)

        # 3. Activation
        x = self.activation(x)

        # 4. Selective SSM
        y = self.selective_scan(x)

        # 5. Gating (SiLU(z) * y)
        y = y * self.activation(z)

        # 6. Output Projection
        out = self.out_proj(y)
        return out

    def selective_scan(self, u):
        """
        Computes the Selective Scan (Algorithm 2 in the paper).
        Note: This is a slow pure-PyTorch implementation. 
        Production requires a CUDA kernel (Scan).
        
        u: shape (B, L, D_inner)
        """
        b, l, d = u.shape
        n = self.d_state

        # Parameters generation from input u
        # x_proj maps (B, L, D) -> (B, L, dt_rank + 2*N)
        x_dbl = self.x_proj(u)  
        
        # Split into dt, B, C
        dt, B, C = torch.split(x_dbl, [self.dt_rank, n, n], dim=-1)
        
        dt = self.dt_proj(dt)  # (B, L, D)
        dt = F.softplus(dt)    # Ensure positive Delta

        # Discretization
        # A is (D, N)
        A = -torch.exp(self.A_log.float()) 
        
        # dA = exp(dt * A) -> (B, L, D, N)
        # Broadcasting dt (B, L, D) against A (D, N)
        dA = torch.exp(torch.einsum("bld,dn->bldn", dt, A))
        
        # dB = dt * B -> (B, L, D, N)
        # B is (B, L, N), broadcast against D
        dB = torch.einsum("bld,bln->bldn", dt, B)

        # Run Scan (Sequential Loop for correctness in pure Torch)
        h = torch.zeros(b, d, n, device=u.device)
        ys = []
        
        for t in range(l):
            # h_t = \bar{A}_t * h_{t-1} + \bar{B}_t * x_t
            # u[:, t] is (B, D) -> unsqueeze to (B, D, 1) broadcast to (B, D, N)
            
            h = dA[:, t] * h + dB[:, t] * u[:, t].unsqueeze(-1)
            
            # y_t = C_t * h_t + D * u_t
            # C[:, t] is (B, N)
            y = torch.einsum("bdn,bn->bd", h, C[:, t])
            y = y + u[:, t] * self.D
            ys.append(y)

        # Stack outputs -> (B, L, D)
        y = torch.stack(ys, dim=1)
        return y
