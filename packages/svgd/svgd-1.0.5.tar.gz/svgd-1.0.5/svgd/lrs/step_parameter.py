from svgd.states import StateForLR
from svgd.lrs import LR

from torch import Tensor
from torch.nn import Module, Parameter

from typing_extensions import Optional, Callable


class StepParameterLR(LR, Module):
    def __init__(
        self,
        lr: Tensor,
        activation: Optional[Callable[[Tensor], Tensor]] = None,
    ):
        """
        Args:
            lr (Tensor): Step-size for each step, (max_n_steps,). Usually, log step-size with exp as an activation.
            activation (Optional[Callable[[Tensor], Tensor]]): Activation function.
        """

        assert lr.dim() == 1

        Module.__init__(self)
        self.lr = Parameter(lr)
        self.activation = activation

    def forward(self, state: StateForLR) -> Tensor:
        if self.lr.shape[0] < state.n_steps:
            raise Exception("More steps than $\\epsilon^l$.")

        lr = self.lr[state.step]

        if self.activation is not None:
            lr = self.activation(lr)

        return lr
