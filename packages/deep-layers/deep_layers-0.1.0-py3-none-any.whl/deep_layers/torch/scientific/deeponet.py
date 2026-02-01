import torch
import torch.nn as nn

class DeepONetLayer(nn.Module):
    """
    Lu et al., 'Learning nonlinear operators: The DeepONet architecture', Nature Machine Intelligence 2021.
    
    Purpose
    -------
    Learns mappings between infinite-dimensional function spaces (operators).
    
    Description
    -----------
    Uses two sub-networks (Branch and Trunk) to compute the dot product of embeddings.
    
    Logic
    -----
        1. Branch Net: Encodes input function samples (sensors).
    2. Trunk Net: Encodes output locations (coordinates).
    3. Output: Dot product of Branch and Trunk embeddings.
    """
    def __init__(self, branch_features, trunk_features, activation=nn.Tanh(), use_bias=True):
        """
        DeepONet implementation based on Lu Lu et al. (2020).
        Implements the "Unstacked DeepONet" architecture (Fig 1D).

        Args:
            branch_features (list): List of layer sizes for Branch Net [input_dim, hidden..., output_dim].
            trunk_features (list): List of layer sizes for Trunk Net [input_dim, hidden..., output_dim].
            activation (nn.Module): Activation function class instance.
            use_bias (bool): Whether to add the final bias b0 (Eq. 2 in paper).
        """
        super(DeepONetLayer, self).__init__()
        
        self.use_bias_final = use_bias
        
        # Check consistency of 'p' (latent dimension)
        if branch_features[-1] != trunk_features[-1]:
            raise ValueError(f"Output dimension of Branch ({branch_features[-1]}) "
                             f"and Trunk ({trunk_features[-1]}) must match.")

        # --- Build Branch Net ---
        branch_layers = []
        for i in range(len(branch_features) - 2):
            branch_layers.append(nn.Linear(branch_features[i], branch_features[i+1]))
            branch_layers.append(activation)
        # Last layer: Linear projection to p
        branch_layers.append(nn.Linear(branch_features[-2], branch_features[-1]))
        self.branch_net = nn.Sequential(*branch_layers)

        # --- Build Trunk Net ---
        trunk_layers = []
        for i in range(len(trunk_features) - 2):
            trunk_layers.append(nn.Linear(trunk_features[i], trunk_features[i+1]))
            trunk_layers.append(activation)
        # Last layer: Linear projection to p (or activation, depending on specific variant).
        # Standard implementation often keeps the merge layer linear.
        trunk_layers.append(nn.Linear(trunk_features[-2], trunk_features[-1]))
        # Note: Some versions apply activation to the trunk output before the dot product.
        # If strict adherence to Eq 1 (tk = sigma(...)) is desired, uncomment next line:
        # trunk_layers.append(activation) 
        self.trunk_net = nn.Sequential(*trunk_layers)

        # --- Final Bias b0 ---
        if self.use_bias_final:
            self.b0 = nn.Parameter(torch.tensor(0.0))

    def forward(self, u_input, y_input):
        """
        Args:
            u_input: Tensor of shape (batch_size, m)
            y_input: Tensor of shape (batch_size, d)
        """
        # b shape: (batch_size, p)
        b = self.branch_net(u_input)
        
        # t shape: (batch_size, p)
        t = self.trunk_net(y_input)
        
        # --- Eq. 2: Dot product + bias ---
        # Element-wise multiplication followed by sum over feature dimension p
        output = torch.sum(b * t, dim=1, keepdim=True)
        
        if self.use_bias_final:
            output = output + self.b0
            
        return output
