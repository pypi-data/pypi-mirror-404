import torch
import torch.nn as nn
import math

class GCNLayer(nn.Module):
    """
    Kipf & Welling, 'Semi-Supervised Classification with Graph Convolutional Networks', ICLR 2017.
    
    Purpose
    -------
    Performs convolution on non-grid structures (graphs) to aggregate neighborhood information.
    
    Description
    -----------
    A first-order approximation of spectral graph convolution using a normalized adjacency matrix.
    
    Logic
    -----
        1. Inputs: Node features H and Adjacency A.
    2. Compute normalized adjacency: D^(-1/2) Ã D^(-1/2).
    3. Aggregate: H' = σ(Â H W).
    """
    def __init__(self, in_features, out_features, bias=True):
        super(GCNLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Weight matrix (W in Eq. 2)
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
            
        self.reset_parameters()

    def reset_parameters(self):
        # Initialization method described in the paper (Glorot/Xavier uniform)
        stdv = 1. / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)
        if self.bias is not None:
            self.bias.data.uniform_(-stdv, stdv)

    def forward(self, input_features, adj):
        """
        Args:
            input_features: Input node features (N x C_in)
            adj: Normalized adjacency matrix (N x N)
        """
        # Step 1: Linear transformation (H * W)
        support = torch.mm(input_features, self.weight)
        
        # Step 2: Neighborhood aggregation (Adj * Support)
        # Using torch.spmm (sparse matrix multiplication) is recommended for efficiency 
        # if adj is a sparse tensor, otherwise torch.mm works for dense.
        if adj.is_sparse:
            output = torch.spmm(adj, support)
        else:
            output = torch.mm(adj, support)
        
        if self.bias is not None:
            return output + self.bias
        else:
            return output

    def __repr__(self):
        return self.__class__.__name__ + ' (' \
               + str(self.in_features) + ' -> ' \
               + str(self.out_features) + ')'
