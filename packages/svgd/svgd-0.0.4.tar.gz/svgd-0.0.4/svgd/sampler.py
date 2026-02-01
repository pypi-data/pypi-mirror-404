from svgd.distributions import TargetDistribution, InitialDistribution
from svgd.kernels import Kernel
from svgd.lrs import LR
from svgd.callbacks import Callback
from svgd.states import StateValues

import torch
from torch.nn import Module
from torch.autograd import grad

from contextlib import nullcontext
from typing_extensions import Literal, List

DivergenceControl = Literal[None, "truncation", "metropolis-hastings"]
HutchinsonDistribution = Literal["rademacher", "normal"]
Event = Literal[
    "on_initialization_done",
    "on_sampling_iteration_started",
    "on_score_computed",
    "on_proposal_computed",
    "on_sampling_iteration_done",
    "on_sampling_done",
]


class SVGD(StateValues, Module):
    def __init__(
        self,
        target_distribution: TargetDistribution,
        initial_distribution: InitialDistribution,
        kernel: Kernel,
        lr: LR,
        divergence_control: DivergenceControl = None,
        hutchinson_distribution: HutchinsonDistribution = "rademacher",
        bound_lr: bool = False,
        lr_bound_alpha: float = 0.9,
        ij_term_update_kernel: bool = False,
        ij_term_density: bool = False,
        ij_term_density_kernel: bool = False,
        track_convergence: bool = False,
        callbacks: List[Callback] = [],
        leaky_lr_clamp: bool = False,
        target_is_score: bool = False,
    ):
        """
        Args:
            target_distribution (TargetDistribution): The target distribution.
            initial_distribution (InitialDistribution): The initial distribution.
            kernel (Kernel): The kernel function.
            lr (LR): The step-size.
            divergence_control (Literal['truncation', 'metropolis-hastings'] | None): Divergence control mechanism.
            hutchinson_distribution (Literal['rademacher', 'normal']): The distribution to use for Hutchinson's estimator.
            bound_lr (bool): Whether to bound the step-size or not.
            ij_term_density (bool): Whether to include the correction term or not.
            track_convergence (bool): Whether to compute the KSD or not.
            callbacks (List[Callback]): List of `Callback`s.
            leaky_lr_clamp (bool): Whether the clamp for the step-size bound is leaky or hard.
            target_is_score (bool): Whether the `TargetDistribution` provides an implementation for `score` instead of `log_prob`.
        """

        Module.__init__(self)

        self.target_distribution = target_distribution
        self.initial_distribution = initial_distribution
        self.kernel = kernel
        self.lr = lr
        self.divergence_control: DivergenceControl = divergence_control
        self.hutchinson_distribution = hutchinson_distribution
        self.bound_lr = bound_lr
        self.lr_bound_alpha = lr_bound_alpha
        self.ij_term_update_kernel = ij_term_update_kernel
        self.ij_term_density = ij_term_density
        self.ij_term_density_kernel = ij_term_density_kernel
        self.track_convergence = track_convergence
        self.callbacks = callbacks
        self.leaky_lr_clamp = leaky_lr_clamp
        self.target_is_score = target_is_score

        self.context_null = nullcontext()
        self.context_no_grad = torch.no_grad()
        self.context_manager = self.context_null

        self.set_default_state_values()

    def sample_with_log_q(self, n_particles: int, n_steps: int):
        """
        Args:
            n_particles (int): Number of particles per batch.
            n_steps (int): Maximum number of steps.

        Returns:
            particles (Tensor): Sampled particles, (..., n, d).
            mask (Tensor): 0-1 Tensor, (..., n). When divergence_control is "truncation", it indicates which particles have been eliminated.
            log_q (Tensor): Particles' log densities, (..., n).
        """
        return self.sample(
            n_particles=n_particles,
            n_steps=n_steps,
            with_log_q=True,
        )

    def sample(
        self,
        n_particles: int,
        n_steps: int,
        with_log_q: bool = False,
    ):
        """
        Args:
            n_particles (int): Number of particles per batch.
            n_steps (int): Maximum number of steps.
            with_log_q (bool): Whether to compute particles' densities.

        Returns:
            particles (Tensor): Sampled particles, (..., n, d).
            mask (Tensor): 0-1 Tensor, (..., n). When divergence_control is "truncation", it indicates which particles have been eliminated.
            log_q (Optional[Tensor]): Particles' log densities, (..., n).
        """

        self.step = -1
        self.n_steps = n_steps
        self.x = self.initial_distribution.rsample(n_particles)

        if with_log_q:
            self.log_q = self.initial_distribution.log_prob(self.x)

        self.initialize_flags(with_log_q)
        self.initialize_masks()
        self.cur_n_particles = self.mask.sum(-1)

        self.call_callback("on_initialization_done")

        for self.step in range(self.n_steps):
            self.call_callback("on_sampling_iteration_started")
            self.update_context_manager()
            self.compute_score_values()
            self.compute_kernel_values()
            self.compute_phi()
            self.compute_tr_j_phi()
            self.compute_tr_j_phi_t_j_phi()
            self.compute_lr()
            self.compute_log_abs_det_j()
            self.compute_svgd_proposal()
            self.call_callback("on_proposal_computed")
            self.apply_divergence_control()
            self.update_log_q()
            self.compute_stein_identity()
            self.call_callback("on_sampling_iteration_done")

            if self.f_break_sampling_loop:
                break

        self.call_callback("on_sampling_done")

        return self.x, self.mask, self.log_q

    def initialize_flags(self, with_log_q: bool):
        self.f_dc_none = self.divergence_control is None
        self.f_dc_truncation = self.divergence_control == "truncation"
        self.f_dc_mh = self.divergence_control == "metropolis-hastings"

        self.f_bound_lr = self.bound_lr

        self.f_has_callbacks = len(self.callbacks) > 0

        self.f_with_log_q = with_log_q
        self.f_attach_iteration = with_log_q

        self.f_break_sampling_loop = False
        self.f_compute_stein_identity = self.track_convergence

        self.f_compute_log_abs_det_j = self.f_with_log_q or self.f_dc_mh

        self.f_compute_tr_j_phi = (
            self.f_compute_log_abs_det_j
            or self.f_bound_lr
            or self.f_compute_stein_identity
        )
        self.f_compute_tr_j_phi_t_j_phi = self.f_bound_lr

        self.f_k_compute_k_xi = (
            self.f_compute_tr_j_phi or self.f_compute_tr_j_phi_t_j_phi
        )
        self.f_k_compute_tr_k_xj_xi = self.f_compute_tr_j_phi
        self.f_k_compute_score_t_k_xk_xi_k_xi = self.f_compute_tr_j_phi_t_j_phi
        self.f_k_compute_tr_k_xj_xi_t_k_xk_xi = self.f_compute_tr_j_phi_t_j_phi
        self.f_k_compute_v_t_k_xj_xi_grad_v_score = (
            self.f_compute_tr_j_phi_t_j_phi and self.ij_term_density
        )

        self.f_compute_tr_j_score = self.f_compute_tr_j_phi and self.ij_term_density
        self.f_compute_grad_v_score = self.f_compute_tr_j_score or (
            self.f_compute_tr_j_phi_t_j_phi and self.ij_term_density
        )

    def initialize_masks(self):
        if self.mask.shape == self.x.shape[:-1]:
            self.mask[...] = 1.0
            self.mask = self.mask.to(self.x.device).to(self.x.dtype)
        else:
            self.mask = torch.ones(
                self.x.shape[:-1], device=self.x.device, dtype=self.x.dtype
            )

        if self.mask_off_diagonal.shape[-1] != self.x.shape[-2]:
            self.mask_off_diagonal = (
                torch.eye(self.x.shape[-2], device=self.x.device, dtype=self.x.dtype)
                .mul(-1)
                .add(1)
            )
        else:
            self.mask_off_diagonal = self.mask_off_diagonal.to(self.x.device).to(
                self.x.dtype
            )

    def call_callback(self, event: Event):
        if not self.f_has_callbacks:
            return

        for callback in self.callbacks:
            getattr(callback, event)(self)

    def update_context_manager(self):
        if self.f_attach_iteration:
            self.context_manager = self.context_null
        else:
            self.context_manager = self.context_no_grad

    def compute_score_values(self):
        if self.target_is_score:
            self.score = self.target_distribution.score(self)

        else:
            self.log_p = self.target_distribution.log_prob(self.x)
            self.score = grad(
                self.log_p.sum(),
                self.x,
                create_graph=self.f_compute_grad_v_score or self.f_attach_iteration,
            )[0]

        self.call_callback("on_score_computed")

        if self.f_compute_grad_v_score:
            if self.hutchinson_distribution == "rademacher":
                self.v = torch.randn_like(self.score).sign()
            elif self.hutchinson_distribution == "normal":
                self.v = torch.randn_like(self.score)
            else:
                raise NotImplementedError()

            self.grad_v_score = grad(
                self.v.mul(self.score).sum(),
                self.x,
                create_graph=self.f_compute_tr_j_score and self.f_attach_iteration,
            )[0]

            if self.f_compute_tr_j_score:
                self.tr_j_score = self.v.mul(self.grad_v_score).sum(-1)

    def compute_kernel_values(self):
        (
            self.k,
            self.k_xj,
            self.k_xi,
            self.tr_k_xj_xi,
            self.score_t_k_xk_xi_k_xi,
            self.tr_k_xj_xi_t_k_xk_xi,
            self.v_t_k_xj_xi_grad_v_score,
        ) = self.kernel.forward(self)

    def compute_phi(self):
        with self.context_manager:
            k_xj = self.mask.unsqueeze(-2).unsqueeze(-1).mul(self.k_xj)

            if not self.ij_term_update_kernel:
                k_xj = self.mask_off_diagonal.unsqueeze(-1).mul(k_xj)

            # sum of drift terms
            self.s_1 = self.k.matmul(self.mask.unsqueeze(-1).mul(self.score))

            # sum of repulsion terms
            self.s_2 = k_xj.sum(-2)

            self.phi = self.s_1.add(self.s_2).div(
                self.cur_n_particles.unsqueeze(-1).unsqueeze(-1)
            )

    def compute_tr_j_phi(self):
        if not self.f_compute_tr_j_phi:
            return

        with self.context_manager:
            k_xi_score = self.score.unsqueeze(-3).mul(self.k_xi).sum(-1)

            if not self.ij_term_density:
                self.tr_j_phi = (
                    k_xi_score.add(self.tr_k_xj_xi)
                    .mul(self.mask_off_diagonal)
                    .mul(self.mask.unsqueeze(-2))
                    .sum(-1)
                    .div(self.cur_n_particles.sub(1).unsqueeze(-1))
                )

            else:
                tr_k_xj_xi = self.tr_k_xj_xi

                if not self.ij_term_density_kernel:
                    tr_k_xj_xi = tr_k_xj_xi.mul(self.mask_off_diagonal)

                tr_j_phi_1 = (
                    k_xi_score.add(tr_k_xj_xi).mul(self.mask.unsqueeze(-2)).sum(-1)
                )
                tr_j_phi_2 = (
                    self.k.diagonal(0, -2, -1).mul(self.tr_j_score).mul(self.mask)
                )
                self.tr_j_phi = tr_j_phi_1.add(tr_j_phi_2).div(
                    self.cur_n_particles.unsqueeze(-1)
                )

    def compute_tr_j_phi_t_j_phi(self):
        if not self.f_compute_tr_j_phi_t_j_phi:
            return

        # a is the drift term and b is the repulsion term

        with torch.no_grad():
            self.compute_tr_b_b_t()
            self.compute_tr_a_b_t()
            self.compute_tr_a_t_a()

        self.tr_j_phi_t_j_phi = self.tr_a_t_a

        if self.ij_term_density:
            self.tr_j_phi_t_j_phi = (
                self.tr_a_b_t.mul(2).add(self.tr_b_b_t).add(self.tr_j_phi_t_j_phi)
            )

    def compute_tr_b_b_t(self):
        if not self.ij_term_density:
            return

        self.tr_b_b_t = (
            self.grad_v_score.pow(2)
            .sum(-1)
            .mul(self.k.diagonal(0, -2, -1).pow(2))
            .mul(self.mask)
            .div(self.cur_n_particles.pow(2).unsqueeze(-1))
        )

    def compute_tr_a_b_t(self):
        if not self.ij_term_density:
            return

        tr_a_b_t_1 = self.v.matmul(self.score.transpose(-2, -1))
        tr_a_b_t_2 = self.grad_v_score.unsqueeze(-2).mul(self.k_xi).sum(-1)
        tr_a_b_t_3 = self.v_t_k_xj_xi_grad_v_score

        if not self.ij_term_density_kernel:
            tr_a_b_t_3 = self.mask_off_diagonal.mul(tr_a_b_t_3)

        self.tr_a_b_t = (
            tr_a_b_t_1.mul(tr_a_b_t_2)
            .add(tr_a_b_t_3)
            .mul(self.mask.unsqueeze(-2))
            .sum(-1)
            .mul(self.k.diagonal(0, -2, -1))
            .mul(self.mask)
            .div(self.cur_n_particles.pow(2).unsqueeze(-1))
        )

    def compute_tr_a_t_a(self):
        tr_a_t_a_1_1 = self.score.matmul(self.score.transpose(-2, -1)).unsqueeze(-3)
        tr_a_t_a_1_2 = self.k_xi.matmul(self.k_xi.transpose(-2, -1))
        tr_a_t_a_1 = tr_a_t_a_1_1.mul(tr_a_t_a_1_2)
        tr_a_t_a_2 = self.score_t_k_xk_xi_k_xi.mul(2)
        tr_a_t_a_3 = self.tr_k_xj_xi_t_k_xk_xi

        if not self.ij_term_density_kernel:
            tr_a_t_a_2 = self.mask_off_diagonal.unsqueeze(-2).mul(tr_a_t_a_2)
            tr_a_t_a_3 = (
                self.mask_off_diagonal.unsqueeze(-1)
                .mul(self.mask_off_diagonal.unsqueeze(-2))
                .mul(tr_a_t_a_3)
            )

        self.tr_a_t_a = (
            tr_a_t_a_1.add(tr_a_t_a_2)
            .add(tr_a_t_a_3)
            .mul(self.mask.unsqueeze(-2).unsqueeze(-1))
            .mul(self.mask.unsqueeze(-2).unsqueeze(-3))
            .sum((-2, -1))
            .div(self.cur_n_particles.pow(2).unsqueeze(-1))
        )

    def compute_lr(self):
        """
        Compute the step-size and apply the step-size bound.
        """

        with self.context_manager:
            self.lr_value = self.lr.forward(self).add(0.0)

        if not self.f_bound_lr:
            self.lr_bound = self.lr_value
            self.corrected_lr_value = self.lr_value
            return

        with torch.no_grad():
            m = self.tr_j_phi.div(self.x.shape[-1]).abs()
            s_squared = self.tr_j_phi_t_j_phi.div(self.x.shape[-1]).sub(m.pow(2)).abs()
            self.lr_bound = (
                s_squared.mul(self.x.shape[-1] - 1)
                .sqrt()
                .add(m)
                .add(1e-5)
                .pow(-1)
                .mul(self.lr_bound_alpha)
                .min(-1)
                .values
            )

        if self.leaky_lr_clamp:
            lr_bound = self.lr_bound
            self.corrected_lr_value = torch.where(
                self.lr_value.lt(lr_bound),
                self.lr_value,
                self.lr_value.sub(lr_bound).mul(-1e-5).add(lr_bound).clamp(min=0),
            )

        else:
            self.corrected_lr_value = self.lr_value.clamp(max=self.lr_bound)

    def compute_log_abs_det_j(self):
        if not self.f_compute_log_abs_det_j:
            return

        self.log_abs_det_j = self.corrected_lr_value.unsqueeze(-1).mul(self.tr_j_phi)

    def compute_svgd_proposal(self):
        self.x_svgd = (
            self.corrected_lr_value.unsqueeze(-1)
            .unsqueeze(-1)
            .mul(self.phi)
            .add(self.x)
        )

    def apply_divergence_control(self):
        if self.f_dc_none:
            self.x = self.x_svgd

        elif self.f_dc_truncation:
            self.mask = self.initial_distribution.is_within_bounds(self.x_svgd).mul(
                self.mask
            )
            self.x = self.x_svgd
            self.cur_n_particles = self.mask.sum(-1)

            if self.cur_n_particles.lt(2).any():
                raise Exception("Less than 2 particles left!")

        elif self.f_dc_mh:
            if self.target_is_score:
                raise Exception()

            with self.context_manager:
                self.log_p_acc = (
                    self.target_distribution.log_prob(self.x_svgd)
                    .sub(self.log_p)
                    .add(self.log_abs_det_j)
                    .clamp(max=0.0)
                )

            self.p_acc = self.log_p_acc.exp()
            self.p_rej = self.p_acc.mul(-1).add(1)
            u = torch.rand_like(self.log_p_acc)
            self.mask_mh = self.p_acc.ge(u)
            self.x = torch.where(self.mask_mh.unsqueeze(-1), self.x_svgd, self.x)

        else:
            raise NotImplementedError()

    def update_log_q(self):
        if not self.f_with_log_q:
            return

        if self.f_dc_none or self.f_dc_truncation:
            self.log_q = self.log_q.sub(self.log_abs_det_j)

        elif self.f_dc_mh:
            if self.target_is_score:
                raise Exception()

            self.log_q = torch.logaddexp(
                self.log_p_acc.sub(self.log_abs_det_j),
                self.p_rej.add(1e-8).log(),
            ).add(self.log_q)

        else:
            raise NotImplementedError()

    def compute_stein_identity(self):
        if not self.f_compute_stein_identity:
            return

        with torch.no_grad():
            self.stein_identity = (
                self.score.mul(self.phi)
                .sum(-1)
                .add(self.tr_j_phi)
                .sum(-1)
                .div(self.cur_n_particles)
                .abs()
                .sqrt()
            )

    def set_default_state_values(self):
        empty = torch.empty(0)

        ################################
        # state on initialization done #
        ################################

        self.n_steps = -1
        self.cur_n_particles = empty

        self.x = empty
        self.mask = empty
        self.log_q = empty
        self.mask_off_diagonal = empty

        #######################################
        # state on sampling iteration started #
        #######################################

        self.step = -1

        ###########################
        # state on score computed #
        ###########################

        self.log_p = empty
        self.score = empty

        ##################################
        # state on score values computed #
        ##################################

        self.v = empty
        self.grad_v_score = empty
        self.tr_j_score = empty

        ####################################
        # state on kernel values computed  #
        ####################################

        self.k = empty
        self.k_xj = empty
        self.k_xi = empty
        self.tr_k_xj_xi = empty
        self.score_t_k_xk_xi_k_xi = empty
        self.tr_k_xj_xi_t_k_xk_xi = empty
        self.v_t_k_xj_xi_grad_v_score = empty

        ################################
        # state on phi values computed #
        ################################

        self.s_1 = empty
        self.s_2 = empty
        self.phi = empty

        self.tr_j_phi = empty

        self.tr_a_t_a = empty
        self.tr_a_b_t = empty
        self.tr_b_b_t = empty
        self.tr_j_phi_t_j_phi = empty

        ########################
        # state on lr computed #
        ########################

        self.lr_value = empty
        self.lr_bound = empty
        self.corrected_lr_value = empty

        ##############################
        # state on proposal computed #
        ##############################

        self.x_svgd = empty
        self.log_abs_det_j = empty

        ##################################
        # state on divergence controlled #
        ##################################

        self.log_p_acc = empty
        self.p_acc = empty
        self.p_rej = empty
        self.mask_mh = empty

        ####################################
        # state on sampling iteration done #
        ####################################

        self.stein_identity = empty
