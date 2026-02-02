from svgd.states import StateForKernel
from svgd.kernels.parameters import KP

from torch import Tensor
from torch.nn import Module, Linear

from typing_extensions import Optional, Callable


class ParameterGNN(KP, Module):
    def __init__(
        self,
        dim_in: int,
        dim_hidden: int,
        activation: Optional[Callable[[Tensor], Tensor]] = None,
    ):

        Module.__init__(self)

        self.activation = activation

        self.l1 = Linear(dim_in, dim_hidden)
        self.l2 = Linear(dim_hidden, dim_hidden)
        self.l3 = Linear(dim_hidden, 1)

    def forward(self, state: StateForKernel, **kwargs) -> Tensor:
        x = state.x

        l1 = self.l1.forward(x.mean(-2)).relu()
        l2 = self.l2.forward(l1).relu()
        l3 = self.l3.forward(l2)

        if self.activation is not None:
            l3 = self.activation(l3)

        return l3.squeeze(-1)
