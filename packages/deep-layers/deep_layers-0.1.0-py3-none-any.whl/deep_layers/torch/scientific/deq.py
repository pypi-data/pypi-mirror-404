import torch
import torch.nn as nn

class DEQLayer(nn.Module):
    def __init__(self, f_module, max_iter=50, tol=1e-3):
        super(DEQLayer, self).__init__()
        self.cell = f_module
        self.f = f_module 
        self.max_iter = max_iter
        self.tol = tol

    def forward(self, x):
        z_init = torch.zeros_like(x)
        # Pass parameters to apply to ensure they are tracked by the autograd engine
        return DEQFunction.apply(self.f, x, z_init, self.max_iter, self.tol, *self.f.parameters())

class DEQFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, f, x, z_init, max_iter, tol, *params):
        ctx.f = f
        ctx.max_iter = max_iter
        ctx.tol = tol
        with torch.no_grad():
            z = z_init
            for _ in range(max_iter):
                z_next = f(z, x)
                if torch.max(torch.abs(z_next - z)) < tol:
                    break
                z = z_next
        ctx.save_for_backward(x, z)
        return z

    @staticmethod
    def backward(ctx, grad_output):
        x, z_star = ctx.saved_tensors
        f = ctx.f
        z_star = z_star.detach().requires_grad_(True)
        
        with torch.enable_grad():
            z_next = f(z_star, x)

        y = grad_output.clone()
        with torch.no_grad():
            for _ in range(ctx.max_iter):
                vjp = torch.autograd.grad(z_next, z_star, y, retain_graph=True)[0]
                y_next = grad_output + vjp
                if torch.max(torch.abs(y_next - y)) < ctx.tol:
                    break
                y = y_next

        with torch.enable_grad():
            params = tuple(f.parameters())
            grads = torch.autograd.grad(z_next, (x,) + params, y)
            grad_x = grads[0]
            grad_params = grads[1:]

        return (None, grad_x, None, None, None) + grad_params
