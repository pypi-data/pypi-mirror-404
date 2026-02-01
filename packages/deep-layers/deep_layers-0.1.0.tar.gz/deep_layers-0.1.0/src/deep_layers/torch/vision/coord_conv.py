import torch
import torch.nn as nn

class CoordConv(nn.Module):
    """
    Liu et al., 'An Intriguing Failing of Convolutional Neural Networks and the CoordConv Solution', NeurIPS 2018.
    
    Purpose
    -------
    Gives translation-invariant CNNs location awareness (e.g., for Generative/RL tasks).
    
    Description
    -----------
    Concatenates coordinate channels (i, j) to the input feature map before applying convolution.
    
    Logic
    -----
    1. Input: (N, C, H, W).
    2. Generate meshgrid xx (range H) and yy (range W).
    3. Normalize coordinates to [-1, 1].
    4. Concatenate: (N, C+2, H, W).
    5. Apply standard Conv2d.
    """

    def __init__(self, in_channels, out_channels, kernel_size, with_r=False, **kwargs):
        super().__init__()
        self.add_coords = AddCoords(with_r=with_r)
        
        # Calculate input channels for the internal conv
        # +2 for x,y coordinates. +1 extra if radius is included.
        extra_channels = 3 if with_r else 2
        
        self.conv = nn.Conv2d(in_channels + extra_channels, out_channels, kernel_size, **kwargs)

    def forward(self, x):
        ret = self.add_coords(x)
        ret = self.conv(ret)
        return ret

class AddCoords(nn.Module):
    def __init__(self, with_r=False):
        super().__init__()
        self.with_r = with_r

    def forward(self, input_tensor):
        """
        Args:
            input_tensor: shape (batch, channel, x_dim, y_dim)
        """
        batch_size, _, x_dim, y_dim = input_tensor.size()

        # Create meshgrid
        # 'ij' indexing ensures x varies along dim 0, y along dim 1
        xx_channel, yy_channel = torch.meshgrid(
            torch.arange(x_dim), 
            torch.arange(y_dim),
            indexing='ij'
        )

        # Normalize to [-1, 1]
        # Note: Avoid division by zero if dim=1, though unlikely in conv settings
        xx_channel = xx_channel.float() / (x_dim - 1)
        yy_channel = yy_channel.float() / (y_dim - 1)

        xx_channel = xx_channel * 2 - 1
        yy_channel = yy_channel * 2 - 1

        # Reshape to (1, 1, x_dim, y_dim) to broadcast over batch
        xx_channel = xx_channel.view(1, 1, x_dim, y_dim).repeat(batch_size, 1, 1, 1)
        yy_channel = yy_channel.view(1, 1, x_dim, y_dim).repeat(batch_size, 1, 1, 1)

        # Move to same device as input
        if input_tensor.is_cuda:
            xx_channel = xx_channel.cuda()
            yy_channel = yy_channel.cuda()

        # Concatenate
        ret = torch.cat([input_tensor, xx_channel, yy_channel], dim=1)

        if self.with_r:
            rr = torch.sqrt(torch.pow(xx_channel, 2) + torch.pow(yy_channel, 2))
            ret = torch.cat([ret, rr], dim=1)

        return ret
