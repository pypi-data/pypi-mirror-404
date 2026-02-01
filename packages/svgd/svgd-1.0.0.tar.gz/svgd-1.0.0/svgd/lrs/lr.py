from svgd.states import StateForLR

from torch import Tensor


class LR:
    def forward(self, state: StateForLR) -> Tensor:
        """
        Args:
            state (StateForLr)

        Returns:
            lr (Tensor): step-size, (...,)

        Notes:
            The leading dimensions denoted by `...` are batch dimensions and must be equal to the batch dimensions of `state.x`.
        """
        raise NotImplementedError()
