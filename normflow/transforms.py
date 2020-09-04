import torch
import numpy as np
from . import flows

# Transforms to be applied to data as preprocessing

class Logit(flows.Flow):
    """
    Logit mapping of image tensor, see RealNVP paper
    logit(alpha + (1 - alpha) * x) where logit(x) = log(x / (1 - x))
    """
    def __init__(self, alpha=0.05, jitter=True, jitter_scale=1./255):
        """
        Constructor
        :param alpha: Alpha parameter, see above
        :param jitter: Flag whether to apply jittering
        :param jitter_scale: Scale of jittering if applicable
        """
        super().__init__()
        self.alpha = alpha
        self.jitter = jitter
        self.jitter_scale = jitter_scale

    def forward(self, z):
        if self.jitter:
            beta = (1 - self.alpha) / (1 + self.jitter_scale)
        else:
            beta = 1 - self.alpha
        sum_dims = list(range(1, z.dim()))
        ls = torch.sum(torch.nn.functional.logsigmoid(z), dim=sum_dims)
        mls = torch.sum(torch.nn.functional.logsigmoid(-z), dim=sum_dims)
        log_det = -np.log(beta) * np.prod([*z.shape[1:]]) + ls + mls
        z = (torch.sigmoid(z) - self.alpha) / beta
        return z, log_det

    def inverse(self, z):
        # Apply scale jittering if needed
        if self.jitter:
            eps = torch.rand_like(z) * self.jitter_scale
            beta = (1 - self.alpha) / (1 + self.jitter_scale)
            z = self.alpha + beta * (z + eps)
        else:
            beta = 1 - self.alpha
            z = self.alpha + beta * z
        logz = torch.log(z)
        log1mz = torch.log(1 - z)
        z = logz - log1mz
        sum_dims = list(range(1, z.dim()))
        log_det = np.log(beta) * np.prod([*z.shape[1:]]) \
                  - torch.sum(logz, dim=sum_dims) \
                  - torch.sum(log1mz, dim=sum_dims)
        return z, log_det