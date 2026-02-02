from svgd.callbacks import Callback
from svgd.states import StateOnSamplingIterationStarted


class Detacher(Callback):
    """
    Callback that controls whether a sampling iteration is attached to the
    computational graph.

    An iteration is attached if:
    - Its step index is a multiple of `freq`, or
    - It is the final iteration and `attach_final_step` is True.
    """

    def __init__(self, freq: int, attach_final_step: bool):
        """
        Args:
            freq (bool): Every `freq`th step, tensor operations will not be tracked in the computational graph
            attach_final_step (bool): Whether the final step should be tracked in the computational graph
        """
        self.freq = freq
        self.attach_final_step = attach_final_step

    def on_sampling_iteration_started(self, state: StateOnSamplingIterationStarted):
        state.f_attach_iteration = (state.step % self.freq == 0) or (
            self.attach_final_step and (state.step == state.n_steps - 1)
        )
