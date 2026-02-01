import torch
import torch.nn as nn

class PhyCRNetLayer(nn.Module):
    """
    Fan et al., 'Physics-informed convolutional-recurrent neural networks for solving PDEs', CMAME 2022.
    
    Purpose
    -------
    Solves spatiotemporal PDEs by encoding physical constraints into the ConvRNN cell.
    
    Description
    -----------
    A ConvRNN where the hidden state update respects physical discretization schemes.
    
    Logic
    -----
    1. Convolutional encoder for spatial features.
    2. Recurrent update rule mimics PDE time-stepping (e.g., u_t+1 = u_t + Δt · Model(u_t)).
    3. Enforce boundary conditions explicitly.
    """

    def __init__(self, input_dim, hidden_dim, kernel_size, bias=True, padding_mode='circular'):
        """
        Args:
            input_dim: Number of channels in input tensor.
            hidden_dim: Number of channels in hidden state.
            kernel_size: Size of the convolving kernel.
            bias: Whether to add a bias term.
            padding_mode: 'circular' for Periodic BCs, or 'zeros', 'reflect', etc.
        """
        super(PhyCRNetLayer, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        self.padding_mode = padding_mode
        self.bias = bias

        # The paper describes convolving [Xt, Ht-1]. 
        # We optimize by performing one large convolution and splitting the results 
        # for input(i), forget(f), cell(c), and output(o) gates.
        self.conv = nn.Conv2d(
            in_channels=self.input_dim + self.hidden_dim,
            out_channels=4 * self.hidden_dim,
            kernel_size=self.kernel_size,
            padding=self.padding,
            padding_mode=self.padding_mode, 
            bias=self.bias
        )

    def forward(self, input_tensor, cur_state=None):
        """
        Args:
            input_tensor: (B, input_dim, H, W)
            cur_state: tuple containing (h_cur, c_cur)
                       h_cur: (B, hidden_dim, H, W)
                       c_cur: (B, hidden_dim, H, W)
        """
        if cur_state is None:
            cur_state = self.init_hidden(input_tensor.size(0), input_tensor.shape[2:])
        h_cur, c_cur = cur_state

        # Eq (2): Concatenate input and previous hidden state along channel dimension
        # Corresponds to [Xt, ht-1] in the paper
        combined = torch.cat([input_tensor, h_cur], dim=1)  

        # Apply convolution
        combined_conv = self.conv(combined)

        # Split the output into 4 parts: input, forget, cell_candidate, output
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)

        # Eq (2) Activation functions
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g) # This corresponds to C_tilde in Eq 2

        # Eq (2) State updates
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)

        return h_next, c_next

    def init_hidden(self, batch_size, image_size):
        height, width = image_size
        return (torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
                torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device))
