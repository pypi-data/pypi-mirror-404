from svgd.states import StateForLR
from svgd.lrs import LR

from torch import Tensor
from torch.nn import Module, Parameter

from typing_extensions import Optional, Callable


class ParameterLR(LR, Module):
    def __init__(
        self, lr: Tensor, activation: Optional[Callable[[Tensor], Tensor]] = None
    ):
        """
        Args:
            lr (Tensor): Step-size, (...,). Usually, log step-size with exp as an activation.
            activation (Optional[Callable[[Tensor], Tensor]]): Activation function.
        """

        Module.__init__(self)
        self.lr = Parameter(lr)
        self.activation = activation

    def forward(self, state: StateForLR) -> Tensor:
        lr = self.lr

        if self.activation is not None:
            lr = self.activation(lr)

        return lr
