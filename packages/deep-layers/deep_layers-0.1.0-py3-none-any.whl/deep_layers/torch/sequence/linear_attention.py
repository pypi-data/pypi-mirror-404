import torch
import torch.nn as nn
import torch.nn.functional as F 
class LinearAttentionLayer(nn.Module):
    """
    Katharopoulos et al., 'Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention', ICML 2020.
    
    Purpose
    -------
    Reduces attention complexity from O(N^2) to O(N) using kernel feature maps.
    
    Description
    -----------
    Replaces softmax with kernel feature map φ(·).
    
    Logic
    -----
        1. Standard Attention: softmax(Q K^T) V.
    2. Linear Attention: φ(Q) (φ(K)^T V).
    3. Maintain running sums Q̂, K̂ for recurrent inference.
    """
    def __init__(self, dim, heads=8, dim_head=64, dropout=0.0):
        super().__init__()
        self.dim = dim
        self.heads = heads
        self.dim_head = dim_head
        self.scale = dim_head ** -0.5
        
        inner_dim = heads * dim_head
        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        
        self.to_out = nn.Sequential(
            nn.Linear(inner_dim, dim),
            nn.Dropout(dropout)
        )

    def feature_map(self, x):
        """
        The paper uses elu(x) + 1 as the feature map formulation
        to ensure non-negative attention weights.
        """
        return F.elu(x) + 1.0

    def forward(self, x, causal=False, mask=None):
        """
        Args:
            x: Input tensor of shape (Batch, SeqLen, Dim)
            causal: If True, uses autoregressive masking (lower triangular)
            mask: Optional padding mask (Batch, SeqLen)
        """
        b, n, _, h = *x.shape, self.heads
        
        # 1. Project Q, K, V
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(lambda t: t.view(b, n, h, -1).transpose(1, 2), qkv)
        # Shapes: (Batch, Heads, SeqLen, DimHead)

        # 2. Apply Feature Map (phi) to Q and K
        # Eq (5) from the paper requires phi(Q) and phi(K)
        q = self.feature_map(q)
        k = self.feature_map(k)

        # 3. Handle Padding Masking (set masked K values to 0)
        if mask is not None:
            mask = mask[:, None, :, None] # Expand for broadcasting
            k.masked_fill_(~mask, 0.)
            v.masked_fill_(~mask, 0.)

        if causal:
            # === Causal Linear Attention (Autoregressive) ===
            # The paper shows this can be computed using cumulative sums (Eq 9-12)
            
            # Compute the KV term: phi(K)^T * V
            # Since we need to maintain sequence history for every step, 
            # we compute the outer product per step and cumsum over sequence.
            
            # einsum notation:
            # b: batch, h: head, n: sequence, d: dim_head (k), e: dim_head (v)
            
            # Numerator term S_i (Eq 10): Sum_{j=1..i} (phi(K_j) * V_j^T)
            # Computed efficiently via cumsum
            k_v = torch.einsum('b h n d, b h n e -> b h n d e', k, v)
            context = k_v.cumsum(dim=2)
            
            # Denominator term Z_i (Eq 11): Sum_{j=1..i} phi(K_j)
            k_cumsum = k.cumsum(dim=2)
            
            # Compute Output (Eq 12)
            # Numerator: phi(Q_i)^T * S_i
            # Denominator: phi(Q_i)^T * Z_i
            
            numerator = torch.einsum('b h n d, b h n d e -> b h n e', q, context)
            denominator = torch.einsum('b h n d, b h n d -> b h n', q, k_cumsum)
            denominator = denominator.unsqueeze(-1) + 1e-6 # Avoid div by zero
            
            out = numerator / denominator

        else:
            # === Non-Causal Linear Attention (Bidirectional) ===
            # This is O(N) because we aggregate K and V globally first.
            
            # Eq (5): Numerator = phi(Q) * (Sum(phi(K)^T * V))
            # Global Context Matrix: Sum over sequence length (n)
            kv = torch.einsum('b h n d, b h n e -> b h d e', k, v)
            
            # Numerator projection
            numerator = torch.einsum('b h n d, b h d e -> b h n e', q, kv)
            
            # Denominator: phi(Q) * Sum(phi(K))^T
            k_sum = k.sum(dim=2) # Sum over sequence
            denominator = torch.einsum('b h n d, b h d -> b h n', q, k_sum)
            denominator = denominator.unsqueeze(-1) + 1e-6
            
            out = numerator / denominator

        # Merge heads and project output
        out = out.transpose(1, 2).reshape(b, n, -1)
        return self.to_out(out)
