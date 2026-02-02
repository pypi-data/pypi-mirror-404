from svgd.callbacks import Callback
from svgd.states import StateOnInitializationDone, StateOnSamplingIterationDone

import torch
from torch import Tensor

from typing import List


class Logger(Callback):
    def __init__(
        self,
        frequency=1,
        log_log_p=False,
        log_score_norm=False,
        log_tr_j_score=False,
        log_drift_term_norm=False,
        log_repulsive_force_norm=False,
        log_phi_norm=False,
        log_lr_value=False,
        log_lr_bound=False,
        log_corrected_lr_value=False,
        log_log_abs_det_j=False,
        log_p_acc=False,
        log_x=False,
        log_stein_identity=False,
        log_log_q=False,
    ):
        """
        Args:
            frequency (bool): Frequency at which to save values.
        """

        self.frequency = frequency
        self.log_log_p = log_log_p
        self.log_score_norm = log_score_norm
        self.log_tr_j_score = log_tr_j_score
        self.log_drift_term_norm = log_drift_term_norm
        self.log_repulsive_force_norm = log_repulsive_force_norm
        self.log_phi_norm = log_phi_norm
        self.log_lr_value = log_lr_value
        self.log_lr_bound = log_lr_bound
        self.log_corrected_lr_value = log_corrected_lr_value
        self.log_log_abs_det_j = log_log_abs_det_j
        self.log_p_acc = log_p_acc
        self.log_x = log_x
        self.log_stein_identity = log_stein_identity
        self.log_log_q = log_log_q

        self.activated = False

    def set_initial_state(self):
        self.log_p: List[float] = []
        self.score_norm: List[float] = []
        self.tr_j_score: List[float] = []
        self.drift_term_norm: List[float] = []
        self.repulsive_force_norm: List[float] = []
        self.phi_norm: List[float] = []
        self.lr_value: List[float] = []
        self.lr_bound: List[float] = []
        self.corrected_lr_value: List[float] = []
        self.log_abs_det_j: List[float] = []
        self.p_acc: List[float] = []
        self.x: List[Tensor] = []
        self.stein_identity: List[float] = []
        self.log_q: List[float] = []

    def on_initialization_done(self, state: StateOnInitializationDone):
        if not self.activated:
            return

        self.set_initial_state()

        if self.log_x:
            self.x.append(state.x.detach().cpu())

    def on_sampling_iteration_done(self, state: StateOnSamplingIterationDone):
        if not self.activated or (
            state.step % self.frequency != 0 and state.step != state.n_steps - 1
        ):
            return

        with torch.no_grad():
            n_particles = state.cur_n_particles.unsqueeze(-1)

            if self.log_log_p:
                self.log_p.append(state.log_p.div(n_particles).sum().item())

            if self.log_score_norm:
                self.score_norm.append(
                    state.score.pow(2).sum(-1).sqrt().div(n_particles).sum().item()
                )

            if self.log_tr_j_score and state.f_compute_tr_j_score:
                self.tr_j_score.append(state.tr_j_score.div(n_particles).sum().item())

            if self.log_drift_term_norm:
                self.drift_term_norm.append(
                    state.s_1.pow(2).sum(-1).sqrt().div(n_particles).sum().item()
                )

            if self.log_repulsive_force_norm:
                self.repulsive_force_norm.append(
                    state.s_2.pow(2).sum(-1).sqrt().div(n_particles).sum().item()
                )

            if self.log_phi_norm:
                self.phi_norm.append(
                    state.phi.pow(2).sum(-1).sqrt().div(n_particles).sum().item()
                )

            if self.log_lr_value:
                self.lr_value.append(state.lr_value.mean().item())

            if self.log_lr_bound:
                self.lr_bound.append(state.lr_bound.mean().item())

            if self.log_corrected_lr_value:
                self.corrected_lr_value.append(state.corrected_lr_value.mean().item())

            if self.log_log_abs_det_j and state.f_compute_log_abs_det_j:
                self.log_abs_det_j.append(
                    state.log_abs_det_j.div(n_particles).sum().item()
                )

            if self.log_p_acc and state.f_dc_mh:
                self.p_acc.append(state.p_acc.div(n_particles).sum().item())

            if self.log_x:
                self.x.append(state.x.detach().cpu())

            if self.log_stein_identity and state.f_compute_stein_identity:
                self.stein_identity.append(state.stein_identity.mean().item())

            if self.log_log_q and state.f_with_log_q:
                self.log_q.append(state.log_q.mean().item())
