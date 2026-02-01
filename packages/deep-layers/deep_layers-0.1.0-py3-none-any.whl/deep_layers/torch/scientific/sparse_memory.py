import torch
import torch.nn as nn
import torch.nn.functional as F

class SparseMemoryLayer(nn.Module):
    """
    Rae et al., 'Scaling Memory-Augmented Neural Networks with Sparse Reads and Writes', 2016.
    
    Purpose
    -------
    Large-scale external memory with sparse access for algorithmic tasks.
    
    Description
    -----------
    NTM-style memory but with sparsity constraints and usage-based allocation.
    
    Logic
    -----
    1. Read/Write using differentiable attention weights.
    2. Enforce sparsity (Top-k selection).
    3. Manage memory allocation and freeing based on usage.
    """
    def __init__(self, input_size, hidden_size, memory_slots, memory_dim, k_sparse=4):
        super(SparseMemoryLayer, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.N = memory_slots  # Number of slots
        self.W = memory_dim    # Dimension of each slot
        self.K = k_sparse      # Sparsity factor (Top-K)

        # Controller: Standard LSTM
        # Input to LSTM is concatenation of external input and previous read vector
        self.controller = nn.LSTMCell(input_size + memory_dim, hidden_size)

        # Output projection layer
        # Outputs: 
        # 1. Query vector q (W)
        # 2. Add vector a (W)
        # 3. Erase vector e (W)
        # 4. Write gate alpha (1)
        # 5. Interpolation gate gamma (1) - mixes prev_read vs LRU
        self.output_projector = nn.Linear(hidden_size, self.W * 3 + 2)
        
        # Final output layer (combination of controller out and read vec)
        self.final_projector = nn.Linear(hidden_size + memory_dim, hidden_size)

    def initial_state(self, batch_size, device):
        """Returns zero-initialized states."""
        # LSTM hidden and cell states
        h_0 = torch.zeros(batch_size, self.hidden_size).to(device)
        c_0 = torch.zeros(batch_size, self.hidden_size).to(device)
        
        # Memory state
        # Usually initialized with small random noise or zeros. 
        # Using small noise to prevent divide-by-zero in cosine sim early on.
        mem_0 = torch.randn(batch_size, self.N, self.W).to(device) * 0.01
        
        # Read weights (sparse)
        wr_0 = torch.zeros(batch_size, self.N).to(device)
        
        # Usage indicator (counter)
        usage_0 = torch.zeros(batch_size, self.N).to(device)
        
        # Previous read vector
        r_0 = torch.zeros(batch_size, self.W).to(device)
        
        return (h_0, c_0), mem_0, wr_0, usage_0, r_0

    def _sparse_read_weights(self, query, memory):
        """
        Calculates Sparse Read Weights using Top-K logic.
        """
        # 1. Content-based addressing (Cosine Similarity)
        # query: [B, W], memory: [B, N, W]
        
        # Normalize for cosine similarity
        q_norm = F.normalize(query, dim=1).unsqueeze(1) # [B, 1, W]
        m_norm = F.normalize(memory, dim=2)             # [B, N, W]
        
        # Similarity scores [B, N]
        sim = torch.sum(q_norm * m_norm, dim=2)
        
        # 2. Sparse Top-K Selection
        # We only keep the top K similarities, masking the rest to -inf (for softmax)
        top_k_vals, top_k_indices = torch.topk(sim, self.K, dim=1)
        
        # Create a mask for scatter
        # Initialize logits with -inf so softmax results in 0 for non-top-k
        logits = torch.full_like(sim, float('-inf'))
        
        # Scatter the top_k values back into the logits tensor
        logits.scatter_(1, top_k_indices, top_k_vals)
        
        # 3. Softmax
        w_r = F.softmax(logits, dim=1) # [B, N] (Sparse, only K non-zeros)
        
        return w_r, top_k_indices

    def forward(self, x, prev_state= None):
        if prev_state is None:
            prev_state = self.initial_state(x.size(0), x.device)
        (h_prev, c_prev), M_prev, wr_prev, usage_prev, r_prev = prev_state
        
        # --- 1. Controller ---
        # Concatenate input and previous read
        lstm_in = torch.cat([x, r_prev], dim=1)
        h_curr, c_curr = self.controller(lstm_in, (h_prev, c_prev))
        
        # Project parameters
        params = self.output_projector(h_curr)
        
        # Slicing parameters
        # Shapes: q: [B, W], a: [B, W], e: [B, W], alpha: [B, 1], gamma: [B, 1]
        q = params[:, :self.W]
        a = params[:, self.W:2*self.W]
        e = torch.sigmoid(params[:, 2*self.W:3*self.W]) # Erase vector in [0,1]
        alpha = torch.sigmoid(params[:, -2:-1])         # Write gate
        gamma = torch.sigmoid(params[:, -1:])           # Interpolation gate

        # --- 2. Read Operation ---
        w_r, top_k_indices = self._sparse_read_weights(q, M_prev)
        
        # Compute read vector: r_t = sum(w(i) * M(i))
        # [B, 1, N] @ [B, N, W] -> [B, 1, W] -> [B, W]
        r_curr = torch.bmm(w_r.unsqueeze(1), M_prev).squeeze(1)
        
        # --- 3. Write Addressing ---
        
        # A. Least Recently Accessed (Usage)
        # Usage logic: increment counter, reset if access > delta
        usage_curr = usage_prev + 1.0
        
        # Define "access" as aggregate of read and write weights. 
        # Note: In the paper, write weights depend on usage, so we use prev_read + prev_write.
        # However, to avoid cyclic dependency in one step, SAM typically uses prev_read and 
        # updates usage AFTER determining the new write location or uses current read.
        # The paper Eq 6: checks if U_t is min.
        
        # We determine "access" based on the current sparse read w_r
        # Reset usage for locations currently read
        # Create a mask for top-k indices
        access_mask = torch.zeros_like(usage_curr).scatter_(1, top_k_indices, 1.0)
        usage_curr = usage_curr * (1 - access_mask) # Reset read locations to 0
        
        # Find Least Recently Used (Max usage value)
        # To get the indicator I_U, we find the argmax of the usage counter
        _, lru_indices = torch.max(usage_curr, dim=1)
        I_U = torch.zeros_like(usage_curr).scatter_(1, lru_indices.unsqueeze(1), 1.0)
        
        # B. Write Weights (Eq 5)
        # w_w = alpha * (gamma * w_r_prev + (1 - gamma) * I_U)
        # Note: Paper says w_r_{t-1}, meaning previous read weights.
        w_w = alpha * (gamma * wr_prev + (1 - gamma) * I_U)
        
        # Apply sparsity to Write Weights?
        # Eq 5 implies w_w is sparse because w_r is sparse (K non-zeros) and I_U is sparse (1 non-zero).
        # So w_w has at most K+1 non-zeros. No extra Top-K needed here.

        # --- 4. Memory Update (Eq 3) ---
        # M_t = M_{t-1} * (1 - w_w * e) + (w_w * a)
        
        # Expand dimensions for broadcasting
        # w_w: [B, N, 1], e: [B, 1, W], a: [B, 1, W]
        w_w_exp = w_w.unsqueeze(2)
        e_exp = e.unsqueeze(1)
        a_exp = a.unsqueeze(1)
        
        # Erase Matrix: [B, N, W]
        erase_matrix = w_w_exp * e_exp
        
        # Add Matrix: [B, N, W]
        add_matrix = w_w_exp * a_exp
        
        # Update
        M_curr = M_prev * (1 - erase_matrix) + add_matrix

        # --- 5. Final Output ---
        out_vec = torch.cat([h_curr, r_curr], dim=1)
        y_out = self.final_projector(out_vec)
        
        next_state = ((h_curr, c_curr), M_curr, w_r, usage_curr, r_curr)
        
        return y_out, next_state
