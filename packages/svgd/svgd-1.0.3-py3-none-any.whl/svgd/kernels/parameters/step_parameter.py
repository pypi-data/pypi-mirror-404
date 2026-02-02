from svgd.states import StateForKernel
from svgd.kernels.parameters import KP

from torch import Tensor
from torch.nn import Module, Parameter

from typing_extensions import Optional, Callable


class StepParameterKP(KP, Module):
    def __init__(
        self,
        kp: Tensor,
        activation: Optional[Callable[[Tensor], Tensor]] = None,
    ):
        assert kp.dim() == 1

        Module.__init__(self)
        self.kp = Parameter(kp)
        self.activation = activation

    def forward(self, state: StateForKernel, **kwargs) -> Tensor:
        if self.kp.shape[0] < state.n_steps:
            raise Exception("More steps than $\\sigma^l$.")

        kp = self.kp[state.step]

        if self.activation is not None:
            kp = self.activation(kp)

        return kp
