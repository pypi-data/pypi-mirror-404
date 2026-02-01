import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np # Fixed NameError

def generate_steerable_basis(kernel_size, in_c, out_c, num_rings, max_freq):
    # For scalar fields, the kernel must be invariant under the group action.
    # We define 2 invariant basis functions: center and the sum of 4 neighbors.
    basis = np.zeros((2, out_c, in_c, kernel_size, kernel_size))
    center = kernel_size // 2
    basis[0, :, :, center, center] = 1.0
    # Sum of 4 neighbors ensures C4 and Reflection invariance
    basis[1, :, :, center-1, center] = 1.0
    basis[1, :, :, center+1, center] = 1.0
    basis[1, :, :, center, center-1] = 1.0
    basis[1, :, :, center, center+1] = 1.0
    return basis
    
class SteerableConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, num_rings=3, max_freq=2):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        basis_numpy = generate_steerable_basis(kernel_size, in_channels, out_channels, num_rings, max_freq)
        self.num_basis_funcs = basis_numpy.shape[0]
        self.register_buffer('basis', torch.tensor(basis_numpy, dtype=torch.float32))
        self.weights = nn.Parameter(torch.randn(self.num_basis_funcs, out_channels, in_channels))
        nn.init.normal_(self.weights, 0, 0.1)

    def get_kernel(self):
        return torch.einsum('boi, boijk -> oijk', self.weights, self.basis)

    def forward(self, x):
        kernel = self.get_kernel()
        return F.conv2d(x, kernel, padding=self.kernel_size//2)
