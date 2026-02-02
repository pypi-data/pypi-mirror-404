from svgd.states import StateForKernel
from svgd.kernels.parameters import KP

from torch import Tensor
from torch.nn import Module, Parameter

from typing_extensions import Optional, Callable


class ParameterKP(KP, Module):
    def __init__(
        self, kp: Tensor, activation: Optional[Callable[[Tensor], Tensor]] = None
    ):
        Module.__init__(self)
        self.kp = Parameter(kp)
        self.activation = activation

    def forward(self, state: StateForKernel, **kwargs) -> Tensor:
        kp = self.kp

        if self.activation is not None:
            kp = self.activation(kp)

        return kp
