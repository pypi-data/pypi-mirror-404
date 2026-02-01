from svgd.distributions import TargetDistribution, InitialDistribution

import torch
from torch import Tensor, Size
from torch.distributions import Distribution


class TorchDistribution(TargetDistribution, InitialDistribution):
    """
    Adapter class for Torch Distributions
    """
    def __init__(self, distribution: Distribution):
        """
        Args:
            distribution (Distribution): Torch Distribution
        """
        super().__init__()
        self.distribution = distribution

    def rsample(self, n_particles: int) -> Tensor:
        try:
            x = self.distribution.rsample(Size((n_particles,)))
        except:
            x = self.distribution.sample(Size((n_particles,)))

        idx = torch.arange(x.dim()).add(1)
        idx[-2], idx[-1] = 0, idx[-1] - 1
        return x.permute(*idx).requires_grad_()

    def log_prob(self, x: Tensor) -> Tensor:
        idx = torch.arange(x.dim()).sub(1)
        idx[0], idx[-1] = -2, idx[-1] + 1
        x = x.permute(*idx)
        idx = torch.arange(x.dim() - 1).add(1).remainder(x.dim() - 1)
        return self.distribution.log_prob(x).permute(*idx)
