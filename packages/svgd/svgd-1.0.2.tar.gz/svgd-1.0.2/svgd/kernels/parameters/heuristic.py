from svgd.states import StateForKernel
from svgd.kernels.parameters import KP

import torch
from torch import Tensor
from torch.nn import Module, Linear

from typing_extensions import Literal

Heuristic = Literal["median", "mean", "fourth", "mmd"]


class HeuristicKP(KP, Module):
    """
    Kernel bandwidth class for different heuristics based on the squared distance between particles.
    """
    def __init__(self, heuristic: Heuristic):
        """
        Args:
            heuristic (Heuristic): One of ["median", "mean", "fourth", "mmd"]
        """

        Module.__init__(self)

        self.heuristic: Heuristic = heuristic
        self._junk = Linear(1, 1)

    def forward(self, state: StateForKernel, **kwargs) -> Tensor:
        mask = state.mask
        n_particles = state.cur_n_particles
        squared_distance: Tensor = kwargs["squared_distance"]

        with torch.no_grad():
            squared_distance = (
                squared_distance.mul(mask.unsqueeze(-1))
                .mul(mask.unsqueeze(-2))
                .flatten(-2, -1)
            )

        if self.heuristic == "mean":
            return (
                squared_distance.nanmean(-1).div(n_particles.add(1).log().mul(2)).sqrt()
            )

        elif self.heuristic == "median":
            return (
                squared_distance.nanmedian(-1)
                .values.div(n_particles.add(1).log().mul(2))
                .sqrt()
            )

        elif self.heuristic == "fourth":
            return (
                squared_distance.nanmean(-1).div(n_particles.add(1).log().mul(4)).sqrt()
            )

        elif self.heuristic == "mmd":
            return squared_distance.sqrt().nanmedian(-1).values.mul(0.1)

        else:
            raise NotImplementedError()
