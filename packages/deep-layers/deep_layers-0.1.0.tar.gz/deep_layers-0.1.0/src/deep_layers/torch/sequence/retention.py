import torch
import torch.nn as nn
import torch.nn.functional as F
class RetentionLayer(nn.Module):
    """
    Sun et al., 'Retentive Network: A Successor to Transformer for Large Language Models', ICLR 2024.
    
    Purpose
    -------
    Supports parallel training, recurrent inference, and chunkwise recurrence (linear complexity).
    
    Description
    -----------
    Reinterprets attention as a recurrent mechanism with multi-scale decay.
    
    Logic
    -----
    1. Compute retention scores using Q, K, V.
    2. Apply cumulative summation (recurrent) or matrix multiplication (parallel).
    3. Apply normalization and gating.
    """
    def __init__(self, embed_dim, num_heads, gate_fn='swish'):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.key_dim = self.head_dim  # Assuming key dim equals value dim for simplicity
        
        # Scaling factor for QK^T / sqrt(d)
        self.scaling = self.key_dim ** -0.5
        
        # Learnable Parameters: W_Q, W_K, W_V
        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        
        # Gating parameter W_G
        self.g_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        
        # Output projection W_O
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        
        # GroupNorm: "normalize the head outputs separately"
        # num_groups = num_heads ensures each head is normalized independently
        self.group_norm = nn.GroupNorm(num_heads, embed_dim)
        
        # Activation for gate
        self.gate_fn = F.silu if gate_fn == 'swish' else F.relu

        # Gamma decay rates (Equation 8)
        # gamma = 1 - 2^(-5 - arange(0, h))
        # We pre-compute these as they are fixed structure, though technically buffers
        gammas = 1 - 2 ** (-5 - torch.arange(0, num_heads, dtype=torch.float32))
        self.register_buffer('gammas', gammas)

    def get_rotary_embedding(self, seq_len, device):
        # Simplified RoPE/xPos implementation for RetNet's Theta
        # Theta_n = e^{i * n * theta}
        inv_freq = 1.0 / (10000 ** (torch.arange(0, self.key_dim, 2, device=device).float() / self.key_dim))
        t = torch.arange(seq_len, device=device).float()
        freqs = torch.einsum('i,j->ij', t, inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()

    def rotate_tensor(self, x, cos, sin):
        # Applies rotary embedding to X
        d = x.shape[-1]
        x1 = x[..., :d//2]
        x2 = x[..., d//2:]
        rotated = torch.cat((-x2, x1), dim=-1)
        return (x * cos) + (rotated * sin)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        
        # 1. Projections
        q = self.q_proj(x) # (B, L, D)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape for multi-head: (B, H, L, d_head)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # 2. Apply Rotary Embeddings (Theta)
        # Note: In RetNet, Q = (X W_Q) * Theta, K = (X W_K) * Theta_conjugate
        cos, sin = self.get_rotary_embedding(seq_len, x.device)
        cos = cos.view(1, 1, seq_len, self.head_dim)
        sin = sin.view(1, 1, seq_len, self.head_dim)
        
        q = self.rotate_tensor(q, cos, sin)
        k = self.rotate_tensor(k, cos, sin)

        # 3. Retention Score: QK^T
        # (B, H, L, d) @ (B, H, d, L) -> (B, H, L, L)
        retention = q @ k.transpose(-2, -1) * self.scaling

        # 4. Decay Mask (D) and Causal Masking
        # D_nm = gamma^(n-m) if n >= m else 0
        n_idx = torch.arange(seq_len, device=x.device).unsqueeze(1) # (L, 1)
        m_idx = torch.arange(seq_len, device=x.device).unsqueeze(0) # (1, L)
        
        # Broadcast gammas to (H, L, L)
        # Power matrix: n - m
        diff = n_idx - m_idx 
        
        # Causal mask logic inside the exponentiation for efficiency:
        # We want gamma^(n-m) where n >= m.
        # Create a mask for causal logic
        causal_mask = (diff >= 0).float()
        
        # Reshape gammas for broadcasting: (H, 1, 1)
        decay_rates = self.gammas.view(self.num_heads, 1, 1)
        
        # Calculate D matrix: (H, L, L)
        # We use abs(diff) because gamma < 1, so gamma^positive is decay.
        # Mask out the future (upper triangle)
        decay_mask = (decay_rates ** diff) * causal_mask
        
        # Add batch dim: (1, H, L, L)
        decay_mask = decay_mask.unsqueeze(0)
        
        # Apply decay mask to retention scores
        retention = retention * decay_mask

        # 5. Output calculation
        # (B, H, L, L) @ (B, H, L, d) -> (B, H, L, d)
        output = retention @ v

        # 6. GroupNorm
        # Reshape back to (B, L, H*d) before GroupNorm
        output = output.transpose(1, 2).contiguous().view(batch_size * seq_len, self.embed_dim)
        output = self.group_norm(output)
        output = output.view(batch_size, seq_len, self.embed_dim)

        # 7. Gating (MSR output)
        # Eq 8: (swish(X W_G) * Y) W_O
        gate = self.gate_fn(self.g_proj(x))
        output = gate * output
        output = self.out_proj(output)

        return output

    def forward_recurrent(self, x, prev_state=None, seq_idx=0):
        """
        Recurrent forward pass for a single timestep (inference).
        
        Args:
            x: Input tensor (Batch, 1, Dim)
            prev_state: Recurrent state (Batch, Heads, HeadDim, HeadDim)
            seq_idx: Current sequence index for RoPE
            
        Returns:
            output: (Batch, 1, Dim)
            state: Updated state
        """
        batch_size, _, _ = x.shape
        
        # 1. Projections
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape (B, 1, H, D_head) -> (B, H, 1, D_head)
        q = q.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 2. RoPE (Computed for single index)
        # Calculate RoPE for just this position
        inv_freq = 1.0 / (10000 ** (torch.arange(0, self.key_dim, 2, device=x.device).float() / self.key_dim))
        t = torch.tensor([seq_idx], device=x.device).float()
        freqs = torch.einsum('i,j->ij', t, inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        cos = emb.cos().view(1, 1, 1, self.head_dim)
        sin = emb.sin().view(1, 1, 1, self.head_dim)
        
        q = self.rotate_tensor(q, cos, sin)
        k = self.rotate_tensor(k, cos, sin)
        
        # 3. Retention Recurrence
        # state = gamma * prev_state + K^T V
        # Outer product K^T V: (B, H, D, 1) @ (B, H, 1, D) -> (B, H, D, D)
        kt_v = k.transpose(-2, -1) @ v 
        
        if prev_state is None:
            prev_state = torch.zeros(batch_size, self.num_heads, self.head_dim, self.head_dim, device=x.device)
            
        # Gamma broadcast: (1, H, 1, 1)
        gamma = self.gammas.view(1, self.num_heads, 1, 1)
        state = prev_state * gamma + kt_v
        
        # Output: (Q @ state) * Scaling
        # (B, H, 1, D) @ (B, H, D, D) -> (B, H, 1, D)
        output = (q @ state) * self.scaling
        
        # 4. GroupNorm
        output = output.transpose(1, 2).contiguous().view(batch_size * 1, self.embed_dim)
        output = self.group_norm(output)
        output = output.view(batch_size, 1, self.embed_dim)
        
        # 5. Gating
        gate = self.gate_fn(self.g_proj(x))
        output = gate * output
        output = self.out_proj(output)
        
        return output, state
