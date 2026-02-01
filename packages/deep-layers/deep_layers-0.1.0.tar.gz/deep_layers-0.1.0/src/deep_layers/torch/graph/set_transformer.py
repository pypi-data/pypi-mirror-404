import torch
import torch.nn as nn
import torch.nn.functional as F
import math

"""
    Lee et al., 'Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks', ICML 2019.
    
    Purpose
    -------
    Attention-based processing of sets with permutation invariance.
    
    Description
    -----------
    Uses inducing points (ISAB) to reduce complexity and seed vectors (PMA) for pooling.
    
    Logic
    -----
        1. ISAB: Standard attention but queries are learnable inducing points.
    2. PMA: Multi-head attention where queries are learnable seed vectors to compress set.
    """
class MAB(nn.Module):
    """
    Multihead Attention Block (MAB) as described in Eq (6) and (7).
    Parameters:
        dim_Q: Dimension of Query
        dim_K: Dimension of Key/Value
        dim_V: Dimension of Value (often same as dim_Q)
        num_heads: Number of attention heads
        ln: Whether to use LayerNorm (default True based on paper)
    """
    def __init__(self, dim_Q, dim_K, dim_V, num_heads, ln=True):
        super(MAB, self).__init__()
        self.dim_V = dim_V
        self.num_heads = num_heads
        
        # Standard Multihead Attention
        # Note: Set Transformer projects Q, K, V. PyTorch's implementation handles this internally.
        self.fc_q = nn.Linear(dim_Q, dim_V)
        self.fc_k = nn.Linear(dim_K, dim_V)
        self.fc_v = nn.Linear(dim_K, dim_V)
        
        if ln:
            self.ln0 = nn.LayerNorm(dim_V)
            self.ln1 = nn.LayerNorm(dim_V)
        self.fc_o = nn.Linear(dim_V, dim_V)

        # Row-wise Feedforward (rFF)
        self.fc1 = nn.Linear(dim_V, dim_V) # In paper, typically expands then compresses, but here kept simple or customizable
        self.fc2 = nn.Linear(dim_V, dim_V)

    def forward(self, Q, K):
        # Q: [batch, n_q, dim_Q]
        # K: [batch, n_k, dim_K]
        
        Q_fc = self.fc_q(Q) 
        K_fc = self.fc_k(K)
        V_fc = self.fc_v(K)

        # Attention mechanism
        # concatenating heads logic is handled inside scaled_dot_product usually, 
        # but here is a manual implementation to ensure exact paper match
        
        dim_split = self.dim_V // self.num_heads
        
        Q_ = torch.cat(Q_fc.split(dim_split, 2), 0)
        K_ = torch.cat(K_fc.split(dim_split, 2), 0)
        V_ = torch.cat(V_fc.split(dim_split, 2), 0)

        # A = softmax(Q * K^T / sqrt(d)) * V
        A = torch.softmax(Q_.bmm(K_.transpose(1, 2)) / math.sqrt(dim_split), 2)
        O = torch.cat((Q_ + A.bmm(V_)).split(Q.size(0), 0), 2)
        
        # LayerNorm(X + Multihead(X, Y, Y)) -> Eq (7)
        O = self.ln0(O)
        
        # LayerNorm(H + rFF(H)) -> Eq (6)
        # rFF is usually Linear -> ReLU -> Linear
        _O = O
        O = self.fc_o(O) # Output projection
        O = self.fc2(F.relu(self.fc1(O)))
        O = self.ln1(_O + O)
        
        return O

class SAB(nn.Module):
    """
    Set Attention Block (SAB) as described in Eq (8).
    SAB(X) = MAB(X, X)
    """
    def __init__(self, dim_in, dim_out, num_heads, ln=True):
        super(SAB, self).__init__()
        self.mab = MAB(dim_in, dim_in, dim_out, num_heads, ln=ln)

    def forward(self, X):
        return self.mab(X, X)

class ISAB(nn.Module):
    """
    Induced Set Attention Block (ISAB) as described in Eq (9) and (10).
    Uses 'm' inducing points to reduce complexity from O(n^2) to O(nm).
    """
    def __init__(self, dim_in, dim_out, num_heads, num_inducing, ln=True):
        super(ISAB, self).__init__()
        self.I = nn.Parameter(torch.Tensor(1, num_inducing, dim_out))
        nn.init.xavier_uniform_(self.I)
        
        # MAB(I, X) -> projects X to H
        self.mab0 = MAB(dim_out, dim_in, dim_out, num_heads, ln=ln)
        # MAB(X, H) -> projects H back to X space
        self.mab1 = MAB(dim_in, dim_out, dim_out, num_heads, ln=ln)

    def forward(self, X):
        # Eq (10): H = MAB(I, X)
        # Broadcast I to batch size
        batch_size = X.size(0)
        I = self.I.repeat(batch_size, 1, 1)
        
        H = self.mab0(I, X)
        
        # Eq (9): ISAB(X) = MAB(X, H)
        return self.mab1(X, H)

class PMA(nn.Module):
    """
    Pooling by Multihead Attention (PMA) as described in Eq (11).
    Aggregates a set into 'k' seed vectors.
    """
    def __init__(self, dim, num_heads, num_seeds, ln=True):
        super(PMA, self).__init__()
        self.S = nn.Parameter(torch.Tensor(1, num_seeds, dim))
        nn.init.xavier_uniform_(self.S)
        self.mab = MAB(dim, dim, dim, num_heads, ln=ln)

    def forward(self, X):
        # Broadcast Seeds to batch size
        batch_size = X.size(0)
        S = self.S.repeat(batch_size, 1, 1)
        
        # PMA_k(Z) = MAB(S, rFF(Z))
        # Note: The rFF inside MAB handles the transformation of Z (the Key/Value)
        return self.mab(S, X)
