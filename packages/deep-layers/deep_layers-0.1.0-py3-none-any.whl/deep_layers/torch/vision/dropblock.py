import torch
import torch.nn as nn
import torch.nn.functional as F

class DropBlock(nn.Module):
    """
    Ghiasi et al., 'DropBlock: A regularization method for convolutional networks', NeurIPS 2018.
    
    Purpose
    -------
    Drops contiguous square regions of feature maps to handle spatial correlation.
    
    Description
    -----------
    Structured dropout where a binary mask is dilated to cover blocks.
    
    Logic
    -----
        1. Sample Centers: Create mask via Bernoulli distribution (γ).
    2. Expand Mask: Apply MaxPool2d (kernel size block_size) to dilate centers into blocks.
    3. Invert & Normalize: 1 - Mask, then scale features to maintain mean.
    """
    r"""
    DropBlock: A regularization method for convolutional networks.
    
    Paper: https://arxiv.org/pdf/1810.12890.pdf
    
    Args:
        drop_prob (float): Probability of dropping a unit (1 - keep_prob). 
                           If scheduler is used, this is the target value.
        block_size (int): Size of the block to drop (width and height).
    """
    def __init__(self, drop_prob=0.1, block_size=7):
        super(DropBlock, self).__init__()
        self.drop_prob = drop_prob
        self.block_size = block_size

    def forward(self, x):
        # 1. Early return if not training or no drop
        if not self.training or self.drop_prob == 0.0:
            return x

        # 2. Get input dimensions
        # N, C, H, W
        gamma = self._compute_gamma(x)
        
        # 3. Sample mask
        # Sample from Bernoulli distribution with probability gamma
        mask = torch.bernoulli(torch.ones_like(x) * gamma)

        # 4. Expand blocks (Dilation)
        # Use Max Pool to expand the 1s (drop seeds) into blocks
        # Padding ensures the output size is the same as input
        mask_block = F.max_pool2d(
            mask, 
            kernel_size=(self.block_size, self.block_size),
            stride=(1, 1),
            padding=(self.block_size // 2, self.block_size // 2)
        )

        # 5. Cropping (to handle even/odd block sizes correctly after padding)
        # If block_size is even, max_pool padding might shift dimensions slightly. 
        if self.block_size % 2 == 0:
            mask_block = mask_block[:, :, :-1, :-1]

        # 6. Invert mask: We want 1s to be kept, 0s to be dropped.
        # Currently 1 represents a "drop block".
        mask_keep = 1 - mask_block

        # 7. Normalize
        # Standard dropout scaling: x * mask / (1 - drop_prob)
        # However, the paper suggests normalizing by exact count: 
        # A = A * count(M) / count_ones(M) (Algorithm 1, line 8)
        # Using standard approximation for computational efficiency:
        normalize_scale = mask_keep.numel() / (mask_keep.sum() + 1e-6)
        
        return x * mask_keep * normalize_scale

    def _compute_gamma(self, x):
        """
        Computes gamma according to Equation 1 in the paper.
        gamma = (drop_prob / block_size**2) * (feat_size**2 / (feat_size - block_size + 1)**2)
        """
        _, _, H, W = x.shape
        feat_area = H * W
        block_area = self.block_size ** 2
        
        # The valid region where a drop block can be centered without going out of bounds
        clipped_h = H - self.block_size + 1
        clipped_w = W - self.block_size + 1
        valid_area = clipped_h * clipped_w

        gamma = (self.drop_prob / block_area) * (feat_area / valid_area)
        return gamma
