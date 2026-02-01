import torch
import torch.nn as nn
import torch.nn.functional as F

class SGRLayer(nn.Module):
    """
    Liang et al., 'Symbolic Graph Reasoning for Semantic Segmentation', NeurIPS 2018.
    
    Purpose
    -------
    Injects external Knowledge Graph information into CNN feature maps to improve semantic consistency.
    
    Description
    -----------
    A three-step process involving voting, reasoning over a semantic graph, and projecting back.
    
    Logic
    -----
        1. Vote: Local features → Semantic Nodes.
    2. Reason: Perform GCN over Semantic Nodes.
    3. Project: Semantic Nodes → Local features.
    """
    def __init__(self, in_channels, num_nodes, node_feature_dim, 
                 adj_matrix, word_embeddings):
        """
        Args:
            in_channels (int): D^l, number of channels in input feature map.
            num_nodes (int): M, number of symbolic nodes.
            node_feature_dim (int): D^c, dimension of symbolic node features.
            adj_matrix (torch.Tensor): (M, M) adjacency matrix of the knowledge graph.
            word_embeddings (torch.Tensor): (M, K) semantic initialization for nodes.
        """
        super(SGRLayer, self).__init__()
        
        self.in_channels = in_channels
        self.num_nodes = num_nodes
        self.node_feature_dim = node_feature_dim
        self.word_emb_dim = word_embeddings.shape[1]
        
        # Register fixed tensors as buffers (not trainable parameters, but part of state)
        # Normalize Adjacency Matrix: D^{-1/2} (A + I) D^{-1/2}
        A_hat = adj_matrix + torch.eye(num_nodes, device=adj_matrix.device)
        D_hat = torch.sum(A_hat, dim=1)
        D_inv_sqrt = torch.pow(D_hat, -0.5)
        D_inv_sqrt[torch.isinf(D_inv_sqrt)] = 0.
        D_mat = torch.diag(D_inv_sqrt)
        norm_adj = torch.mm(torch.mm(D_mat, A_hat), D_mat)
        
        self.register_buffer('adj', norm_adj)
        self.register_buffer('word_embeddings', word_embeddings)

        # --- Module 1: Local-to-Semantic Voting ---
        # Transform local features to vote for nodes: W^a
        self.conv_voting = nn.Conv2d(in_channels, num_nodes, kernel_size=1)
        # Transform local features for node representation: W^{ps}
        self.conv_transform = nn.Conv2d(in_channels, node_feature_dim, kernel_size=1)

        # --- Module 2: Graph Reasoning ---
        # GCN Weight: W^g (Applied to concat of node_feats + word_embs)
        self.gcn_linear = nn.Linear(node_feature_dim + self.word_emb_dim, node_feature_dim)
        
        # --- Module 3: Semantic-to-Local Mapping ---
        # Compatibility metric weights
        self.conv_compatibility_local = nn.Conv2d(in_channels, node_feature_dim, kernel_size=1, bias=False)
        self.linear_compatibility_node = nn.Linear(node_feature_dim, node_feature_dim, bias=False)
        
        # Transform back to local dimensions: W^{sp}
        self.linear_map_back = nn.Linear(node_feature_dim, in_channels)

    def forward(self, x):
        """
        Args:
            x: Input tensor (Batch, Channels, Height, Width)
        Returns:
            out: Output tensor (Batch, Channels, Height, Width)
        """
        batch_size, channels, h, w = x.size()
        
        # -----------------------------------------------------------
        # 1. Local-to-Semantic Voting
        # -----------------------------------------------------------
        
        # A^{ps}: Voting weights (B, M, H, W) -> (B, M, HW)
        voting_map = self.conv_voting(x)
        voting_map = voting_map.view(batch_size, self.num_nodes, -1)
        voting_map = F.softmax(voting_map, dim=1) # Softmax over nodes as per Eq 2 denominator
        
        # Transformed Features: (B, D^c, H, W) -> (B, D^c, HW) -> (B, HW, D^c)
        local_feats = self.conv_transform(x)
        local_feats = local_feats.view(batch_size, self.node_feature_dim, -1).permute(0, 2, 1)
        
        # H^{ps} = Voting * Features -> (B, M, HW) * (B, HW, D^c) = (B, M, D^c)
        node_feats = torch.bmm(voting_map, local_feats)
        
        # -----------------------------------------------------------
        # 2. Graph Reasoning
        # -----------------------------------------------------------
        
        # Concatenate evolved features with static word embeddings
        # word_embeddings: (M, K) -> (B, M, K)
        batch_word_embs = self.word_embeddings.unsqueeze(0).expand(batch_size, -1, -1)
        
        # B = [H^{ps}, S] -> (B, M, D^c + K)
        gcn_input = torch.cat([node_feats, batch_word_embs], dim=2)
        
        # Graph Propagation: H^g = Sigma(A_hat * B * W^g)
        # Step 1: Linear Transform (B * W^g) -> (B, M, D^c)
        gcn_transformed = self.gcn_linear(gcn_input)
        
        # Step 2: Multiply by Adjacency Matrix
        # (M, M) * (B, M, D^c) -> (B, M, D^c)
        # We perform matmul over the node dimensions
        node_feats_evolved = torch.matmul(self.adj, gcn_transformed)
        node_feats_evolved = F.relu(node_feats_evolved)
        
        # -----------------------------------------------------------
        # 3. Semantic-to-Local Mapping
        # -----------------------------------------------------------
        
        # Compute Compatibility (Attention)
        # Project local x to query space: (B, D^c, H, W)
        query = self.conv_compatibility_local(x).view(batch_size, self.node_feature_dim, -1) # (B, D^c, HW)
        
        # Project nodes to key space: (B, M, D^c)
        key = self.linear_compatibility_node(node_feats_evolved) # (B, M, D^c)
        
        # Attention scores: (B, HW, D^c) * (B, D^c, M) -> (B, HW, M)
        # Transpose query to (B, HW, D^c) and key to (B, D^c, M) for bmm
        attn_logits = torch.bmm(query.permute(0, 2, 1), key.permute(0, 2, 1))
        
        # Normalize compatibility map
        attn_weights = F.softmax(attn_logits, dim=2) # (B, HW, M)
        
        # Map nodes back to channel space W^{sp}: (B, M, D^c) -> (B, M, C)
        values = self.linear_map_back(node_feats_evolved)
        
        # Weighted sum: (B, HW, M) * (B, M, C) -> (B, HW, C)
        out_global = torch.bmm(attn_weights, values)
        
        # Reshape to (B, C, H, W)
        out_global = out_global.permute(0, 2, 1).view(batch_size, channels, h, w)
        
        # Residual Connection
        return F.relu(out_global + x)
