import torch
import torch.nn as nn
import torch.nn.functional as F

class VQLayer(nn.Module):
    def __init__(self, num_embeddings, embedding_dim, commitment_cost=0.25):
        super(VQLayer, self).__init__()
        self._num_embeddings = num_embeddings
        self._embedding_dim = embedding_dim
        self._commitment_cost = commitment_cost
        self._embedding = nn.Embedding(self._num_embeddings, self._embedding_dim)
        # Expose for tests
        self.embedding = self._embedding 
        self._embedding.weight.data.uniform_(-1/self._num_embeddings, 1/self._num_embeddings)

    def forward(self, inputs):
        input_shape = inputs.shape
        flat_input = inputs.permute(0, 2, 3, 1).contiguous()
        flat_input = flat_input.view(-1, self._embedding_dim)
        
        distances = (torch.sum(flat_input**2, dim=1, keepdim=True) 
                    + torch.sum(self._embedding.weight**2, dim=1)
                    - 2 * torch.matmul(flat_input, self._embedding.weight.t()))
            
        encoding_indices = torch.argmin(distances, dim=1).unsqueeze(1)
        quantized = self._embedding(encoding_indices).view_as(flat_input)
        
        quantized = quantized.view(input_shape[0], input_shape[2], input_shape[3], input_shape[1])
        quantized = quantized.permute(0, 3, 1, 2).contiguous()
        
        e_latent_loss = F.mse_loss(quantized, inputs.detach())
        q_latent_loss = F.mse_loss(quantized.detach(), inputs)
        loss = q_latent_loss + self._commitment_cost * e_latent_loss
        quantized = inputs + (quantized - inputs).detach()
        
        encodings = torch.zeros(encoding_indices.shape[0], self._num_embeddings, device=inputs.device)
        encodings.scatter_(1, encoding_indices, 1)
        avg_probs = torch.mean(encodings, dim=0)
        perplexity = torch.exp(-torch.sum(avg_probs * torch.log(avg_probs + 1e-10)))
        
        return loss, quantized, perplexity, encoding_indices
