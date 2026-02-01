import torch
import torch.nn as nn

class NTNLayer(nn.Module):
    """
    Socher et al., 'Reasoning With Neural Tensor Networks for Knowledge Base Completion', NeurIPS 2013.
    
    Purpose
    -------
    Relational reasoning using a bilinear tensor product.
    
    Description
    -----------
    Computes bilinear tensor products between two entity vectors.
    
    Logic
    -----
        1. For vectors e1, e2 and relation R.
    2. Compute e1^T W_R^{[k]} e2 for k slices of tensor W_R.
    3. Concatenate with linear transformation and apply activation.
    """
    def __init__(self, input_dim, slice_dim):
        """
        Args:
            input_dim (d): The dimension of the entity vectors.
            slice_dim (k): The number of slices in the tensor.
        """
        super(NTNLayer, self).__init__()
        self.input_dim = input_dim
        self.slice_dim = slice_dim

        # The Tensor W: shape (d, d, k)
        # Using Parameter to allow manual handling in einsum
        self.W = nn.Parameter(torch.Tensor(input_dim, input_dim, slice_dim))

        # The Standard Matrix V: shape (k, 2d) and Bias b (k,)
        # nn.Linear handles Wx + b internally. 
        # Input to Linear is 2d, output is k.
        self.V_layer = nn.Linear(2 * input_dim, slice_dim, bias=True)

        # The Output Vector u: shape (k, 1)
        # Usually u acts as a dot product projection, effectively a Linear layer with output 1
        self.u_layer = nn.Linear(slice_dim, 1, bias=False)

        self.reset_parameters()

    def reset_parameters(self):
        # Initialize parameters similarly to Xavier/Glorot
        nn.init.xavier_uniform_(self.W)
        nn.init.xavier_uniform_(self.V_layer.weight)
        nn.init.zeros_(self.V_layer.bias)
        nn.init.xavier_uniform_(self.u_layer.weight)

    def forward(self, e1, e2):
        """
        Args:
            e1: Entity 1 vectors (batch_size, input_dim)
            e2: Entity 2 vectors (batch_size, input_dim)
        """
        
        # 1. Bilinear Tensor Product: e1^T * W * e2
        # einsum: batch(b), dim(i), dim(j), slices(k)
        # e1(b,i), W(i,j,k), e2(b,j) -> result(b,k)
        tensor_product = torch.einsum('bi,ijk,bj->bk', e1, self.W, e2)

        # 2. Standard Feed Forward: V * [e1, e2] + b
        concatenated = torch.cat((e1, e2), dim=1) # Shape (batch, 2d)
        standard_product = self.V_layer(concatenated) # Shape (batch, k)

        # 3. Combine: (Tensor + Standard + b)
        # Note: Bias b is already included in self.V_layer
        hidden_layer = tensor_product + standard_product

        # 4. Nonlinearity: f = tanh
        activated_hidden = torch.tanh(hidden_layer)

        # 5. Final Score: u^T * hidden
        score = self.u_layer(activated_hidden)

        return score
