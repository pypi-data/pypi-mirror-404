import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class KANLayer(nn.Module):
    def __init__(self, in_features, out_features, grid_size=5, spline_order=3, scale_noise=0.1, 
                 scale_base=1.0, scale_spline=1.0, enable_standalone_scale_spline=True, 
                 base_activation=torch.nn.SiLU, grid_eps=0.02, grid_range=[-1, 1]):
        super(KANLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.grid_size = grid_size
        self.spline_order = spline_order

        h = (grid_range[1] - grid_range[0]) / grid_size
        grid = (torch.arange(-spline_order, grid_size + spline_order + 1) * h + grid_range[0]).expand(in_features, -1).contiguous()
        self.register_buffer("grid", grid)

        self.base_weight = nn.Parameter(torch.Tensor(out_features, in_features))
        self.spline_weight = nn.Parameter(torch.Tensor(out_features, in_features, grid_size + spline_order))
        self.enable_standalone_scale_spline = enable_standalone_scale_spline
        if enable_standalone_scale_spline:
            self.spline_scaler = nn.Parameter(torch.Tensor(out_features, in_features))
        
        self.scale_noise = scale_noise
        self.scale_base = scale_base
        self.scale_spline = scale_spline
        self.base_activation = base_activation()
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.base_weight, a=math.sqrt(5) * self.scale_base)
        if self.enable_standalone_scale_spline:
            nn.init.ones_(self.spline_scaler)
        with torch.no_grad():
            grid_points = self.grid.T[self.spline_order : -self.spline_order]
            noise = (torch.rand(grid_points.shape[0], self.in_features, self.out_features) - 0.5) * self.scale_noise / self.grid_size
            self.spline_weight.data.copy_((self.scale_spline if not self.enable_standalone_scale_spline else 1.0) * self.curve2coeff(grid_points, noise))

    def b_splines(self, x: torch.Tensor):
        grid: torch.Tensor = self.grid
        x = x.unsqueeze(-1)
        bases = ((x >= grid[:, :-1]) & (x < grid[:, 1:])).to(x.dtype)
        for k in range(1, self.spline_order + 1):
            t = grid[:, : -(k + 1)]
            val = (x - t) / (grid[:, k:-1] - t + 1e-8) * bases[:, :, :-1]
            t = grid[:, k + 1 :]
            val += (t - x) / (t - grid[:, 1:-k] + 1e-8) * bases[:, :, 1:]
            bases = val
        return bases.contiguous()

    def curve2coeff(self, x: torch.Tensor, y: torch.Tensor):
        A = self.b_splines(x).transpose(0, 1)
        B = y.transpose(0, 1)
        solution = torch.linalg.lstsq(A, B).solution
        return solution.permute(2, 0, 1)

    def forward(self, x: torch.Tensor):
        base_output = F.linear(self.base_activation(x), self.base_weight)
        spline_basis = self.b_splines(x)
        if self.enable_standalone_scale_spline:
            spline_output = torch.einsum("bij,oij,oi->bo", spline_basis, self.spline_weight, self.spline_scaler)
        else:
            spline_output = torch.einsum("bij,oij->bo", spline_basis, self.spline_weight)
        return base_output + spline_output
