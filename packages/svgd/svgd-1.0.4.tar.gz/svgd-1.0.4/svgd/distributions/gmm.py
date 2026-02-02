from svgd.distributions import InitialDistribution

import torch
from torch import Tensor
from torch.nn import Module

from math import log


class GMM(InitialDistribution, Module):
    def __init__(self, mus: Tensor, stdevs: Tensor, weights: Tensor) -> None:
        """
        Args:
            mus (Tensor): Means per class, (k, d)
            stdevs (Tensor): Standard deviations per class, (k, d)
            weights (Tensor); Weight for each class, (k,)
        """
        
        Module.__init__(self)

        assert mus.dim() == stdevs.dim() == weights.dim() + 1 == 2
        assert mus.shape[0] == stdevs.shape[0] == weights.shape[0]
        assert mus.shape[1] == stdevs.shape[1]

        self._k, self._d = mus.shape
        self.mus = torch.nn.Parameter(mus)
        self._log_stdevs = torch.nn.Parameter(stdevs.add(1e-12).log())
        self._weight_logits = torch.nn.Parameter(weights)

    @property
    def stdevs(self) -> Tensor:
        return self._log_stdevs.exp()

    @property
    def weights(self) -> Tensor:
        return self._weight_logits.softmax(-1)

    def log_prob(self, x: Tensor) -> Tensor:
        xc = x.unsqueeze(-2) - self.mus
        log_prob1 = xc.div(self.stdevs).pow(2).sum(-1).div(-2)
        log_prob2 = self._d * log(2 * torch.pi) / (-2)
        log_prob3 = self._log_stdevs.sum(-1).mul(-1)
        log_prob4 = self.weights.log()
        return torch.logsumexp(log_prob1 + log_prob2 + log_prob3 + log_prob4, -1)

    def rsample(self, n_particles: int) -> Tensor:
        idx = torch.multinomial(self.weights, n_particles, replacement=True).view(
            (n_particles,)
        )
        z = torch.randn(n_particles, self._d, device=self.mus.device)
        return self.mus[idx] + z * self.stdevs[idx]

    def is_within_bounds(self, x: Tensor) -> Tensor:
        return x.unsqueeze(-2).sub(self.mus).abs().le(self.stdevs.mul(3)).all(-1).any(-1)
