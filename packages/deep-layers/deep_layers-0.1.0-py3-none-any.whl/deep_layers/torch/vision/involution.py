import torch
import torch.nn as nn

class Involution(nn.Module):
    """
    Li et al., 'Involution: Inverting the Inherence of Convolution for Visual Recognition', CVPR 2021.
    
    Purpose
    -------
    Spatial-specific but channel-agnostic convolution (opposite of standard Conv), reducing redundancy.
    
    Description
    -----------
    Generates kernels dynamically per pixel based on input features.
    
    Logic
    -----
        1. Kernel Generation: Reduce channels (1x1 Conv), then expand to K×K groups.
    2. Unfold Input: Use unfold to get sliding windows.
    3. Multiply & Sum: Element-wise multiplication of Input Windows × Generated Kernels, sum over K×K.
    """
    def __init__(self, channels, kernel_size=7, stride=1, group_channels=16, reduction_ratio=4):
        """
        Involution Layer Implementation (PyTorch)
        
        Args:
            channels (int): Number of input/output channels.
            kernel_size (int): Size of the involution kernel (default: 7).
            stride (int): Stride of the operation.
            group_channels (int): Number of channels per group sharing the same kernel 
                                  (default: 16, as per paper ablation).
            reduction_ratio (int): Reduction ratio for the channel reduction in kernel generation.
        """
        super(Involution, self).__init__()
        
        self.kernel_size = kernel_size
        self.stride = stride
        self.channels = channels
        self.reduction_ratio = reduction_ratio
        self.group_channels = group_channels
        
        # Calculate number of groups (G in paper)
        self.groups = self.channels // self.group_channels
        
        # Define padding to maintain 'same' spatial dimensions (if stride=1)
        self.padding = kernel_size // 2

        # 1. Kernel Generation Path (phi function in paper)
        # Reduce channels -> Non-linearity -> Expand to produce kernels
        self.reduce = nn.Conv2d(
            in_channels=channels, 
            out_channels=channels // reduction_ratio, 
            kernel_size=1
        )
        
        self.span = nn.Conv2d(
            in_channels=channels // reduction_ratio, 
            out_channels=kernel_size * kernel_size * self.groups, 
            kernel_size=1
        )
        
        self.initial_mapping = nn.AvgPool2d(stride, stride) if stride > 1 else nn.Identity()
        self.bn = nn.BatchNorm2d(channels // reduction_ratio)
        self.relu = nn.ReLU(inplace=True)
        
        # Unfold layer to extract sliding local blocks from input
        self.unfold = nn.Unfold(
            kernel_size=kernel_size, 
            dilation=1, 
            padding=self.padding, 
            stride=stride
        )

    def forward(self, x):
        # x: (Batch, Channels, Height, Width)
        batch_size, _, height, width = x.shape
        
        # --- Kernel Generation ---
        # 1. Downsample if stride > 1 (AvgPool)
        x_down = self.initial_mapping(x)
        
        # 2. Generate kernels: (B, C, H, W) -> (B, K*K*G, H, W)
        # Eq 6 in paper: W1 * sigma(W0 * x)
        kernel_gen = self.span(self.relu(self.bn(self.reduce(x_down))))
        
        # Get output dimensions based on kernel generation (handles striding)
        kernel_h, kernel_w = kernel_gen.shape[-2:]
        
        # Reshape to separate groups and kernel spatial dims
        # Shape: (B, G, K*K, H_out, W_out) -> flatten spatial: (B, G, K*K, N) where N=H*W
        kernel_gen = kernel_gen.view(
            batch_size, self.groups, self.kernel_size**2, kernel_h, kernel_w
        ).flatten(3)
        
        # Add a dimension for broadcasting over channels within a group
        # Shape: (B, G, 1, K*K, N)
        kernel_gen = kernel_gen.unsqueeze(2)

        # --- Data Path ---
        # Extract sliding windows
        # Shape: (B, C*K*K, N)
        x_unfolded = self.unfold(x)
        
        # Reshape to match kernel structure
        # Shape: (B, G, C//G, K*K, N)
        x_unfolded = x_unfolded.view(
            batch_size, self.groups, self.group_channels, self.kernel_size**2, -1
        )

        # --- Involution Operation ---
        # Multiply kernels with data and sum over the kernel spatial dimension (K*K)
        # Eq 4 in paper
        # (B, G, 1, K*K, N) * (B, G, C//G, K*K, N) -> Sum over dim 3
        out = (kernel_gen * x_unfolded).sum(dim=3)
        
        # Reshape back to image format: (B, C, H_out, W_out)
        out = out.view(batch_size, self.channels, kernel_h, kernel_w)
        
        return out
