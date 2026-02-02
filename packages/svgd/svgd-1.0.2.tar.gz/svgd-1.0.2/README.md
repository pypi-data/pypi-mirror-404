# Metropolis-Hastings Stein Variational Gradient Descent (MET-SVGD)

## Installation

Installing the library requires `python>=3.9`:
```
pip install svgd
```

## Quickstart

```python
from svgd import SVGD
from svgd.distributions import TorchDistribution, Gaussian
from svgd.kernels import RBF
from svgd.kernels.parameters import ParameterKP
from svgd.lrs import ParameterLR

import torch
from torch.optim.adam import Adam
from torch.distributions import MultivariateNormal

from tqdm import tqdm
import matplotlib.pyplot as plt

from math import log, sqrt

device = "cuda:3"
d = 10

# initialize the target distribution
target_distribution = TorchDistribution(
    MultivariateNormal(torch.zeros(d).to(device), torch.eye(d).to(device))
)

# initialize the initial distribution
initial_distribution = Gaussian(torch.ones(d).mul(2), torch.ones(d))

# initialize the kernel
kernel = RBF(
    ParameterKP(
        torch.tensor(1.0).log(),
        lambda x: x.clamp(log(1e-2), log(sqrt(d / 2))).exp(),
    )
)

# initialize the learning rate
lr = ParameterLR(torch.tensor(0.1).log(), lambda x: x.exp())

# initialize the SVGD object
svgd = SVGD(
    target_distribution=target_distribution,
    initial_distribution=initial_distribution.requires_grad_(True),
    kernel=kernel.requires_grad_(True),
    lr=lr.requires_grad_(True),
    divergence_control="metropolis-hastings",
    bound_lr=True,
).to(device)

# initialize the optimizer
optimizer = Adam(svgd.parameters(), 5e-2)

# for statistic collection
loss_hist = []
entropy_hist = []

# main training loop
for _ in tqdm(range(200)):
    # get samples and their log densities
    x, mask, log_q = svgd.sample_with_log_q(n_particles=100, n_steps=100)

    # if only particles are required, call:
    # x, _, _ = svgd.sample(n_particles=100, n_steps=100)

    # estimate the entropy
    entropy = log_q.mul(mask).sum(-1).div(mask.sum(-1)).mul(-1)

    # compute the kld loss
    log_p = target_distribution.log_prob(x).mul(mask).sum(-1).div(mask.sum(-1))
    loss = entropy.add(log_p).mul(-1)

    # update parameters
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()

    loss_hist.append(loss.item())
    entropy_hist.append(entropy.item())
```

## The SVGD Class

The signature of the `__init__` method of the SVGD class is:
```python
def __init__(
    self: Self@SVGD,
    target_distribution: TargetDistribution,
    initial_distribution: InitialDistribution,
    kernel: Kernel,
    lr: LR,
    divergence_control: DivergenceControl = None,
    bound_lr: bool = False,
    track_convergence: bool = False,
    callbacks: List[Callback] = [],
    leaky_lr_clamp: bool = False
) -> None: ...
```

`target_distribution` and `initial_distribution` are explained in depth in the next section.

Using the RBF kernel is explained in the Quickstart example, and creating custom bandwidths and step-sizes is shown with examples in [Section 5](#sec5-ck).

`divergence_control` can be either of `None`, or `metropolis-hastings` (details [here](https://leksandrs.github.io/met-svgd-web/optimizations/#divergence-control-via-metropolis-hastings)).

`bound_lr` controls whether the [step-size condition](https://leksandrs.github.io/met-svgd-web/optimizations/#divergence-control-via-metropolis-hastings) is applied.

`track_convergence` indicates whether or not to compute `self.stein_identity`. Useful with `Callback`s.

`callbacks` is an array of `Callback`s. This is explained in [Callbacks](#callbacks).

`leaky_lr_clamp` indicates whether the `lr_bound` is a hard `clamp` or not. Hard clamping kills gradient flow at the extremes.

## Custom Distributions

```python
from svgd.distributions import TargetDistribution, InitialDistribution

import torch
from torch import Tensor
from torch.nn import Module, Parameter

import matplotlib.pyplot as plt

from math import log, pi
```

To create a custom target distribution, all that is required is to create a class that implements the `TargetDistribution` interface, which can be found in `svgd.distributions`. Similarly for initial distributions.

The following are example target and initial diagonal GMM distributions. I will assume that `means` and `stdevs` both have the shape `(n_components, n_dimensions)` and `weights` is `(n_components,)`. But, of course, as long as your implementation adheres to the interface, your distributions can be as complicated as you require.

```python
class TargetDiagonalGMM(TargetDistribution):
    def __init__(self, means: Tensor, stdevs: Tensor, weights: Tensor):
        assert len(means.shape) == 2
        assert len(weights.shape) == 1
        assert means.shape == stdevs.shape
        assert means.shape[-2] == weights.shape[-1]
        assert stdevs.gt(0.0).all()

        self.means = means
        self.stdevs = stdevs
        self.weights = weights.softmax(-1)

    def log_prob(self, x: Tensor):
        # the input tensor `x` has shape (..., n, d)
        # the bi are optional, hence len(x.shape) is at least 2

        vars = self.stdevs.pow(2)

        return (
            x.unsqueeze(-2)
            .sub(self.means)
            .pow(2)
            .div(vars)
            .add(vars.log())
            .add(log(2 * pi))
            .sum(-1)
            .div(-2)
            .add(self.weights.log())
            .logsumexp(-1)
        )
```

```python
class InitialDiagonalGMM(InitialDistribution, Module):
    def __init__(self, means: Tensor, stdevs: Tensor, weights: Tensor):
        Module.__init__(self)

        assert len(means.shape) == 2
        assert len(weights.shape) == 1
        assert means.shape == stdevs.shape
        assert means.shape[-2] == weights.shape[-1]
        assert stdevs.gt(0.0).all()

        self.means = Parameter(means)
        self.log_stdevs = Parameter(stdevs.log())
        self.logits_weights = Parameter(weights.log_softmax(-1))

    @property
    def stdevs(self):
        return self.log_stdevs.clamp(-5, 2).exp()

    def rsample(self, n_particles: int) -> Tensor:
        stdevs = self.stdevs
        weights = self.logits_weights.softmax(-1)

        idx = torch.multinomial(weights, n_particles, True)

        return (
            torch.randn(n_particles, self.means.shape[-1], device=self.means.device)
            .mul(stdevs[idx])
            .add(self.means[idx])
        )

    def log_prob(self, x: Tensor):
        vars = self.stdevs.pow(2)
        log_weights = self.logits_weights.log_softmax(-1)

        return (
            x.unsqueeze(-2)
            .sub(self.means)
            .pow(2)
            .div(vars)
            .add(vars.log())
            .add(log(2 * pi))
            .sum(-1)
            .div(-2)
            .add(log_weights)
            .logsumexp(-1)
        )
```

## Custom Kernel Bandwidths and Step-Sizes

```python
from svgd.lrs import LR
from svgd.kernels.parameters import KP
from svgd.states import StateForKernel, StateForLR

from torch import Tensor
from torch.nn import Module, Parameter, Linear

from typing_extensions import Union, List
```

The RBF kernel is defined as $$k(x,y) = \exp\left(-\frac{1}{2\sigma^2}||x-y||^2\right).$$

In this library, $\sigma$ is defined as a class that implements the `KP` interface available at `svgd.kernels.parameters`. The interface only requires that a forward method be implemented. It takes `state: StateForKernel` and `**kwargs` as attributes. `state` lists the available quantities on the `SVGD` object.

`sigma` must be a `(...,)` tensor, where the batch dimensions correspond to the batch dimensions of the particles returned by `InitialDistribution.rsample`.

Suppose we decide that we are always going to perform `L` SVGD steps and that `InitialDistribution.rsample` returns a tensor whose shape is `(n, d)`, then a straightforward sigma implementation would be a `(L,)` tensor learnable via gradient descent. At each step, we pick the corresponding $\sigma_l$, whose shape would be `(,)` (i.e. a scalar).

```python
class CustomSigma(KP, Module):
    def __init__(self, sigma: Tensor):
        assert sigma.dim() == 1
        assert sigma.ge(0.0).all()

        Module.__init__(self)

        self.log_sigma = Parameter(sigma.add(1e-5).log())

    def forward(self, state: StateForKernel, **kwargs):
        # state.x has shape (n, d), so the returned tensor should have shape `(,)` (i.e. it should be a scalar)
        return self.log_sigma[state.step].clamp(-10, 10).exp()
```

In other cases, your $\sigma$ will be parametrized by a neural network (e.g. reinforcement learning).
In this case, we can't just inspect the weights to get the current sigma values as we would do with a `Parameter` $\sigma$, since every evaluation gives a different one, but we can track the values the network outputted throughout the SVGD steps.
To that end, you could implement a logger wrapper class.

```python
class SigmaNN(KP, Module):
    def __init__(self, obs_dim: int, hidden_dim: int):
        Module.__init__(self)

        self.obs: Union[None, Tensor] = None  # (..., obs_dim)

        self.l1 = Linear(obs_dim, hidden_dim)
        self.l2 = Linear(hidden_dim, hidden_dim)
        self.log_sigma = Linear(hidden_dim, 1)

    def set_observation(self, obs: Tensor):
        self.obs = obs

    def forward(self, state: StateForKernel, **kwargs):
        if self.obs is None:
            raise Exception()
        
        # in this context, for each `obs`, we have `n` particles
        # therefore, `state.x`'s shape is `(..., n, d)

        l1 = self.l1.forward(self.obs).relu()
        l2 = self.l2.forward(l1).relu()
        sigma = self.log_sigma.forward(l2).clamp(-10, 10).exp()
        
        self.obs = None

        return sigma.squeeze(-1)  # must be (...)
```

```python
class SigmaWithHist(KP, Module):
    def __init__(self, sigma: KP):
        Module.__init__(self)

        self.sigma = sigma
        self.log_sigma = False

    def set_default_state(self):
        self.sigma_hist: List[Tensor] = []

    def forward(self, state: StateForKernel, **kwargs):
        sigma = self.sigma.forward(state, **kwargs)

        if not self.log_sigma:
            return sigma

        if state.step == 0:
            self.set_default_state()

        self.sigma_hist.append(sigma)
```

This can then be used as follows:
```python
sigma = SigmaWithHist(SigmaNN(100, 64))
# ...
svgd = SVGD(kernel=RBF(sigma), ...)

for i in range(n_iter):
    sigma.log_sigma = i % 100 == 0
    obs, ... = ...
    sigma.set_observation(obs)
    x, mask, log_q = svgd.sample_with_log_q(n_particles, n_steps)
    # ... etc
```

Dealing with the learning rate is exactly the same. The interface that should be implemented is `LR`, which can be found at `gamma.svgd.lrs`.
The learning rate, too, must be a `(...)` tensor.
```python
class CustomLR(LR, Module):
    def __init__(self, lr: Tensor):
        assert lr.dim() == 1
        assert lr.ge(0.0).all()

        Module.__init__(self)

        self.log_lr = Parameter(lr.add(1e-5).log())

    def forward(self, state: StateForLR):
        return self.log_lr[state.step].clamp(-10, state.x.shape[-2]).exp()
```

## Callbacks

`Callback` is an abstract `class` defined as:
```python
class Callback:
    def on_initialization_done(self, state: StateOnInitializationDone):
        pass

    def on_sampling_iteration_started(self, state: StateOnSamplingIterationStarted):
        pass

    def on_score_computed(self, state: StateOnScoreComputed):
        pass

    def on_proposal_computed(self, state: StateOnProposalComputed):
        pass

    def on_sampling_iteration_done(self, state: StateOnSamplingIterationDone):
        pass

    def on_sampling_done(self, state: StateOnSamplingDone):
        pass
```

`Callback`s are executed at specified stages identified by states during a given iteration in the following order:
1. `on_initialization_done`
2. `on_sampling_iteration_started`
3. `on_score_computed`
4. `on_proposal_computed`
5. `on_sampling_iteration_done`
6. `on_sampling_done`

For example, the state `StateOnProposalComputed` means that the loop is at the stage where the proposal has been computed and is available in the `state` variable.

Importantly, we expose `f_attach_iteration`, which controls whether or not to detach the gradients during a given iteration (it is set to `False` by default), and `f_break_sampling_loop`, which controls whether to break the sampling loop (e.g. based on the stein identity).

`f_attach_iteration` should be set in `on_sampling_iteration_started`, and `f_break_sampling_loop` before `on_sampling_iteration_done`.

All states are listed under `svgd.states`. Note that they build upon one another.