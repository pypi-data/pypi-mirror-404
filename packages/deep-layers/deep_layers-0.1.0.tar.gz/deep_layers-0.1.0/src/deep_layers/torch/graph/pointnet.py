import torch
import torch.nn as nn
import torch.nn.functional as F

class PointNetSA(nn.Module):
    """
    Qi et al., 'PointNet++: Deep Hierarchical Feature Learning on Point Sets', NeurIPS 2017.
    """
    def __init__(self, npoint, radius, nsample, in_channel, mlp, group_all=False):
        super(PointNetSA, self).__init__()
        self.npoint = npoint
        self.radius = radius
        self.nsample = nsample
        self.group_all = group_all
        
        self.mlp_convs = nn.ModuleList()
        self.mlp_bns = nn.ModuleList()
        last_channel = in_channel + 3 
        
        for out_channel in mlp:
            self.mlp_convs.append(nn.Conv2d(last_channel, out_channel, 1))
            self.mlp_bns.append(nn.BatchNorm2d(out_channel))
            last_channel = out_channel

    def forward(self, xyz, points):
        xyz = xyz.permute(0, 2, 1) # [B, 3, N]
        if points is not None:
            points = points.permute(0, 2, 1) # [B, D, N]

        if self.group_all:
            new_xyz = torch.zeros(xyz.shape[0], 3, 1).to(xyz.device) 
            grouped_xyz = xyz.view(xyz.shape[0], 3, 1, xyz.shape[2])
            if points is not None:
                new_points = torch.cat([grouped_xyz, points.view(points.shape[0], points.shape[1], 1, points.shape[2])], dim=1)
            else:
                new_points = grouped_xyz
        else:
            xyz_trans = xyz.permute(0, 2, 1)
            fps_idx = farthest_point_sample(xyz_trans, self.npoint) 
            new_xyz = index_points(xyz_trans, fps_idx) 
            
            idx = query_ball_point(self.radius, self.nsample, xyz_trans, new_xyz) 
            grouped_xyz = index_points(xyz_trans, idx) 
            grouped_xyz_norm = grouped_xyz - new_xyz.unsqueeze(2)

            if points is not None:
                points_trans = points.permute(0, 2, 1)
                grouped_points = index_points(points_trans, idx) 
                new_points = torch.cat([grouped_xyz_norm, grouped_points], dim=-1) 
            else:
                new_points = grouped_xyz_norm

            new_points = new_points.permute(0, 3, 1, 2)
            new_xyz = new_xyz.permute(0, 2, 1) 

        for i, conv in enumerate(self.mlp_convs):
            bn = self.mlp_bns[i]
            new_points = F.relu(bn(conv(new_points)))

        new_points = torch.max(new_points, 3)[0] 
        
        return new_xyz.permute(0, 2, 1), new_points.permute(0, 2, 1)

def square_distance(src, dst):
    B, N, _ = src.shape
    _, M, _ = dst.shape
    dist = -2 * torch.matmul(src, dst.permute(0, 2, 1))
    dist += torch.sum(src ** 2, -1).view(B, N, 1)
    dist += torch.sum(dst ** 2, -1).view(B, 1, M)
    return dist

def farthest_point_sample(xyz, npoint):
    """
    Input:
        xyz: pointcloud data, [B, N, 3]
        npoint: number of samples
    Return:
        centroids: sampled pointcloud index, [B, npoint]
    """
    device = xyz.device
    B, N, C = xyz.shape
    centroids = torch.zeros(B, npoint, dtype=torch.long).to(device)
    distance = torch.ones(B, N).to(device) * 1e10
    
    # Use a deterministic starting point (index 0) to ensure 
    # batch independence and consistent results across runs.
    farthest = torch.zeros(B, dtype=torch.long).to(device)
    
    batch_indices = torch.arange(B, dtype=torch.long).to(device)
    
    for i in range(npoint):
        centroids[:, i] = farthest
        centroid = xyz[batch_indices, farthest, :].view(B, 1, 3)
        dist = torch.sum((xyz - centroid) ** 2, -1)
        mask = dist < distance
        distance[mask] = dist[mask]
        farthest = torch.max(distance, -1)[1]
    return centroids

def query_ball_point(radius, nsample, xyz, new_xyz):
    device = xyz.device
    B, N, C = xyz.shape
    _, S, _ = new_xyz.shape
    group_idx = torch.arange(N, dtype=torch.long).to(device).view(1, 1, N).repeat([B, S, 1])
    sqrdists = square_distance(new_xyz, xyz)
    group_idx[sqrdists > radius ** 2] = N 
    group_idx = group_idx.sort(dim=-1)[0][:, :, :nsample]
    group_first = group_idx[:, :, 0].view(B, S, 1).repeat([1, 1, nsample])
    mask = group_idx == N
    group_idx[mask] = group_first[mask]
    return group_idx

def index_points(points, idx):
    device = points.device
    B = points.shape[0]
    view_shape = list(idx.shape)
    view_shape[1:] = [1] * (len(view_shape) - 1)
    repeat_shape = list(idx.shape)
    repeat_shape[0] = 1
    batch_indices = torch.arange(B, dtype=torch.long).to(device).view(view_shape).repeat(repeat_shape)
    new_points = points[batch_indices, idx, :]
    return new_points
