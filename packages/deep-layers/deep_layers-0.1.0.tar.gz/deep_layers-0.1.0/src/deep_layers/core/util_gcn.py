import numpy as np
import scipy.sparse as sp

def normalize_adj(adj):
    """
    Implements the renormalization trick: D~^-0.5 * A~ * D~^-0.5
    A~ = A + I
    """
    # 1. Add self-loops (A~ = A + I)
    adj = sp.coo_matrix(adj)
    adj_tilde = adj + sp.eye(adj.shape[0])
    
    # 2. Calculate degree matrix D~
    rowsum = np.array(adj_tilde.sum(1))
    
    # 3. Calculate D~^-0.5
    d_inv_sqrt = np.power(rowsum, -0.5).flatten()
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
    d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
    
    # 4. Result: D~^-0.5 * A~ * D~^-0.5
    return adj_tilde.dot(d_mat_inv_sqrt).transpose().dot(d_mat_inv_sqrt).tocoo()
