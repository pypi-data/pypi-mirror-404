from torch import Tensor

from typing_extensions import Protocol, Optional


class Flags(Protocol):
    f_dc_none: bool
    f_dc_truncation: bool
    f_dc_mh: bool

    f_bound_lr: bool

    f_has_callbacks: bool

    f_with_log_q: bool
    f_attach_iteration: bool

    f_compute_grad_v_score: bool
    f_compute_tr_j_score: bool

    f_k_compute_k_xi: bool
    f_k_compute_tr_k_xj_xi: bool
    f_k_compute_score_t_k_xk_xi_k_xi: bool
    f_k_compute_tr_k_xj_xi_t_k_xk_xi: bool
    f_k_compute_v_t_k_xj_xi_grad_v_score: bool

    f_compute_tr_j_phi: bool
    f_compute_tr_j_phi_t_j_phi: bool

    f_compute_log_abs_det_j: bool

    f_compute_stein_identity: bool
    f_break_sampling_loop: bool


class StateOnInitializationDone(Flags, Protocol):
    n_steps: int
    cur_n_particles: Tensor

    x: Tensor
    mask: Tensor
    log_q: Tensor
    mask_off_diagonal: Tensor


class StateOnSamplingIterationStarted(StateOnInitializationDone, Protocol):
    step: int


class StateOnScoreComputed(StateOnSamplingIterationStarted, Protocol):
    log_p: Tensor
    score: Tensor


class StateOnScoreValuesComputed(StateOnScoreComputed, Protocol):
    v: Tensor
    grad_v_score: Tensor
    tr_j_score: Tensor


class StateForKernel(StateOnScoreValuesComputed, Protocol):
    pass


class StateOnKernelValuesComputed(StateForKernel, Protocol):
    k: Tensor
    k_xj: Tensor
    k_xi: Tensor
    tr_k_xj_xi: Tensor
    score_t_k_xk_xi_k_xi: Tensor
    tr_k_xj_xi_t_k_xk_xi: Tensor
    v_t_k_xj_xi_grad_v_score: Tensor


class StateOnPhiValuesComputed(StateOnKernelValuesComputed, Protocol):
    s_1: Tensor
    s_2: Tensor
    phi: Tensor

    tr_j_phi: Tensor

    tr_a_t_a: Tensor
    tr_a_b_t: Tensor
    tr_b_b_t: Tensor
    tr_j_phi_t_j_phi: Tensor


class StateForLR(StateOnPhiValuesComputed, Protocol):
    pass


class StateOnLRComputed(StateForLR, Protocol):
    lr_value: Tensor
    lr_bound: Tensor
    corrected_lr_value: Tensor


class StateOnProposalComputed(StateOnLRComputed, Protocol):
    log_abs_det_j: Tensor
    x_svgd: Tensor


class StateOnDivergenceControlled(StateOnProposalComputed, Protocol):
    log_p_acc: Tensor
    p_acc: Tensor
    p_rej: Tensor
    mask_mh: Tensor


class StateOnSamplingIterationDone(StateOnDivergenceControlled, Protocol):
    stein_identity: Tensor


class StateOnSamplingDone(StateOnSamplingIterationDone, Protocol):
    pass


class StateValues(StateOnSamplingDone, Protocol):
    pass
