from svgd.states import StateForKernel

from torch import Tensor


class KP:
    def forward(self, state: StateForKernel, **kwargs) -> Tensor:
        """
        Args:
            state (StateForKernel)
        
        Returns:
            Tensor: Kernel bandwidth
        """
        raise NotImplementedError()
