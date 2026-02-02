from svgd.distributions import InitialDistribution

import torch
from torch import Tensor
from torch.nn import Module, Parameter

from math import log


class Gaussian(InitialDistribution, Module):
    def __init__(self, mu: Tensor, stdev: Tensor, threshold: float = 3.0):
        """
        Args:
            mu (Tensor): Means, (d,)
            stdev (Tensor): Standard deviations, (d,)
        """
        Module.__init__(self)

        assert mu.dim() == stdev.dim() == 1
        assert mu.shape[0] == stdev.shape[0]

        (self._d,) = mu.shape
        self.mu = Parameter(mu)
        self._log_stdev = Parameter(stdev.log())
        self.threshold = threshold

    @property
    def stdev(self) -> Tensor:
        return self._log_stdev.exp()

    def rsample(self, n_particles: int) -> Tensor:
        z = torch.randn(n_particles, self._d, device=self.mu.device)
        x = self.mu + z * self._log_stdev.exp()

        if not x.requires_grad:
            x.requires_grad_(True)

        return x

    def log_prob(self, x: Tensor) -> Tensor:
        log_prob1 = (x - self.mu).div(self.stdev).pow(2).sum(-1)
        log_prob2 = self._d * log(2 * torch.pi)
        log_prob3 = self._log_stdev.mul(2).sum(-1)
        return (log_prob1 + log_prob2 + log_prob3).div(-2)

    def is_within_bounds(self, x: Tensor) -> Tensor:
        return torch.all((x - self.mu).abs() <= self.threshold * self.stdev, dim=-1)
