from svgd.lrs import LR
from svgd.states import StateForLR

import torch
from torch import Tensor
from torch.nn import Module, Parameter


class StepLR(LR, Module):
    """
    StepLR models the lr as lr = initial_lr * decay_factor^floor(t / step_size), with a smooth floor function.
    """
    def __init__(self, initial_lr: Tensor, step_size: Tensor, decay_rate: Tensor):
        """
        Args:
            initial_lr (Tensor): Initial lr, (...,).
            step_size (Tensor): Determines the step size of the lr, (...,).
            decay_rate (Tensor): Modulates how quickly the lr decays, (...,).
        """

        Module.__init__(self)

        self._log_initial_lr = Parameter(initial_lr.log())
        self._log_step_size = Parameter(step_size.log())
        self._log_decay_rate = Parameter(decay_rate.log())

    def forward(self, state: StateForLR) -> Tensor:
        gamma = 0.99
        frac = self._log_step_size.mul(-1).exp().mul(state.step)
        arg = frac.mul(torch.pi).mul(2)
        numerator = arg.sin().mul(-gamma)
        denominator = arg.cos().mul(-gamma).add(1)
        arctan_term = numerator.div(denominator).arctan().div(torch.pi)
        floor = frac.sub(0.5).sub(arctan_term)
        return (
            self._log_decay_rate.mul(floor)
            .add(self._log_initial_lr)
            .exp()
            .clamp(max=self._log_initial_lr.exp())
        )
