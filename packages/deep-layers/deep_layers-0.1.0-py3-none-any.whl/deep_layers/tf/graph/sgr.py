import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

class SGRLayer(tf.keras.layers.Layer):
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
    def __init__(self, num_nodes, node_feature_dim, 
                 adj_matrix, word_embeddings, **kwargs):
        """
        Args:
            num_nodes (int): M.
            node_feature_dim (int): D^c.
            adj_matrix (np.array): (M, M) adjacency matrix.
            word_embeddings (np.array): (M, K) semantic vectors.
        """
        super(SGRLayer, self).__init__(**kwargs)
        self.num_nodes = num_nodes
        self.node_feature_dim = node_feature_dim
        
        # Pre-process Adjacency Matrix (GCN Normalization)
        A = adj_matrix + np.eye(num_nodes)
        D = np.sum(A, axis=1)
        D_inv_sqrt = np.power(D, -0.5)
        D_inv_sqrt[np.isinf(D_inv_sqrt)] = 0.
        D_mat = np.diag(D_inv_sqrt)
        self.norm_adj = np.dot(np.dot(D_mat, A), D_mat).astype(np.float32)
        
        self.word_embeddings = word_embeddings.astype(np.float32)
        self.word_emb_dim = word_embeddings.shape[1]

    def build(self, input_shape):
        in_channels = input_shape[-1]
        
        # Module 1: Local-to-Semantic Voting
        self.conv_voting = layers.Conv2D(self.num_nodes, 1, padding='same', name='voting_conv')
        self.conv_transform = layers.Conv2D(self.node_feature_dim, 1, padding='same', name='feat_conv')
        
        # Module 2: Graph Reasoning
        # W^g: maps (Dc + K) -> Dc
        self.gcn_dense = layers.Dense(self.node_feature_dim, name='gcn_linear')
        
        # Module 3: Semantic-to-Local Mapping
        # W^s parts for compatibility
        self.compat_local = layers.Conv2D(self.node_feature_dim, 1, padding='same', use_bias=False, name='compat_local')
        self.compat_node = layers.Dense(self.node_feature_dim, use_bias=False, name='compat_node')
        
        # W^{sp}: Map back to channel dim
        self.map_back = layers.Dense(in_channels, name='map_back')
        
        super().build(input_shape)

    def call(self, inputs):
        # inputs: (B, H, W, C)
        batch_size = tf.shape(inputs)[0]
        h = tf.shape(inputs)[1]
        w = tf.shape(inputs)[2]
        
        # ---------------------------
        # 1. Voting
        # ---------------------------
        # A^{ps}: (B, H, W, M)
        voting_map = self.conv_voting(inputs)
        voting_map = tf.reshape(voting_map, [batch_size, -1, self.num_nodes]) # (B, HW, M)
        voting_map = tf.nn.softmax(voting_map, axis=2) # Softmax over nodes
        
        # Features: (B, H, W, Dc)
        local_feats = self.conv_transform(inputs)
        local_feats = tf.reshape(local_feats, [batch_size, -1, self.node_feature_dim]) # (B, HW, Dc)
        
        # Transpose voting to (B, M, HW) to match matrix mult logic
        voting_map_t = tf.transpose(voting_map, perm=[0, 2, 1])
        
        # Node Feats: (B, M, HW) * (B, HW, Dc) -> (B, M, Dc)
        node_feats = tf.matmul(voting_map_t, local_feats)
        
        # ---------------------------
        # 2. Reasoning
        # ---------------------------
        # Expand static embeddings to batch: (B, M, K)
        emb_expanded = tf.expand_dims(self.word_embeddings, 0)
        emb_expanded = tf.tile(emb_expanded, [batch_size, 1, 1])
        
        # Concat: (B, M, Dc+K)
        gcn_in = tf.concat([node_feats, emb_expanded], axis=-1)
        
        # Linear transform: (B, M, Dc)
        gcn_trans = self.gcn_dense(gcn_in)
        
        # Graph Prop: (M, M) * (B, M, Dc) -> (B, M, Dc)
        # Note: tf.matmul automatically broadcasts the first matrix if rank differs appropriately,
        # but here we can just treat adj as constant.
        evolved_feats = tf.matmul(self.norm_adj, gcn_trans)
        evolved_feats = tf.nn.relu(evolved_feats)
        
        # ---------------------------
        # 3. Mapping
        # ---------------------------
        # Project local X: (B, H, W, Dc) -> (B, HW, Dc)
        query = self.compat_local(inputs)
        query = tf.reshape(query, [batch_size, -1, self.node_feature_dim])
        
        # Project nodes: (B, M, Dc)
        key = self.compat_node(evolved_feats)
        
        # Attention: (B, HW, Dc) * (B, Dc, M) -> (B, HW, M)
        attn_logits = tf.matmul(query, key, transpose_b=True)
        attn_weights = tf.nn.softmax(attn_logits, axis=-1)
        
        # Map back values: (B, M, C)
        values = self.map_back(evolved_feats)
        
        # Weighted sum: (B, HW, M) * (B, M, C) -> (B, HW, C)
        out_global = tf.matmul(attn_weights, values)
        
        # Reshape back to spatial
        out_global = tf.reshape(out_global, [batch_size, h, w, -1])
        
        # Residual
        return tf.nn.relu(inputs + out_global)
