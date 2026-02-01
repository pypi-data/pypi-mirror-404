from svgd.states import StateOnSamplingIterationStarted

from torch import Tensor


class TargetDistribution:
    def log_prob(self, x: Tensor) -> Tensor:
        """
        Args:
            x (Tensor): Samples, (..., n, d)

        Returns:
            Tensor: The log probabilities of x, (..., n)
        """
        raise NotImplementedError()

    def score(self, state: StateOnSamplingIterationStarted) -> Tensor:
        """
        Args:
            state (StateOnSamplingIterationStarted)

        Returns:
            Tensor: The score function evaluated at x, (..., n, d)
        """
        raise NotImplementedError()


class InitialDistribution:
    def rsample(self, n_particles: int) -> Tensor:
        """
        Args:
            n_particles (int)

        Returns:
            Tensor: Samples, (..., n_particles, d)
        """
        raise NotImplementedError()

    def log_prob(self, x: Tensor) -> Tensor:
        """
        Args:
            x (Tensor): Samples, (..., n, d)

        Returns:
            Tensor: The log probabilities of x, (..., n)
        """
        raise NotImplementedError()

    def is_within_bounds(self, x: Tensor) -> Tensor:
        """
        Args:
            x (Tensor): Samples (..., n, d)

        Returns:
            Tensor: A boolean array indicating whether a given particle x is "within the bounds" of the initial distribution, (b1, ..., bm, n)
        """
        raise NotImplementedError()
