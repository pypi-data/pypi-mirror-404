from svgd.callbacks import Callback
from svgd.states import StateOnSamplingIterationDone


class SamplingBreaker(Callback):
    """
    Callback that stops the sampling loop based on the behavior of Stein's identity across iterations.

    The sampling process is terminated under either of the following conditions:

    1. The current Stein identity value falls below a given threshold.
    2. The Stein identity has increased for more than `patience` consecutive
       iterations, indicating lack of convergence or divergence.

    This callback is only active when the flag `svgd.f_compute_stein_identity` is True.
    It assumes that `InitialDistribution.rsample` returns a tensor whose shape is `(n, d)`.
    """

    def __init__(self, threshold: float, patience: int):
        """
        Parameters:
            threshold (float): Sampling stops immediately if the Stein identity falls below this value.
            patience (int): Number of consecutive iterations with increasing Stein identity allowed before stopping the sampling loop.
        """
        self.threshold = threshold
        self.patience = patience

        self.set_default_state()

    def set_default_state(self):
        self.counter = 0
        self.prev = float("inf")

    def on_sampling_iteration_done(self, state: StateOnSamplingIterationDone):
        if not state.f_compute_stein_identity:
            return

        if state.step == 0:
            self.set_default_state()

        if state.x.dim() != 2:
            raise Exception("This class is meant for when `state.x.shape` is `(n, d)`.")

        si = state.stein_identity.item()

        if si < self.threshold:
            state.f_break_sampling_loop = True
            return

        si_diff = si - self.prev
        self.prev = si

        if si_diff > 0:
            self.counter += 1

        else:
            self.counter = 0

        state.f_break_sampling_loop = self.counter > self.patience
