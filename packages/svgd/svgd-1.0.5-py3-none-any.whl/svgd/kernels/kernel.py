from svgd.states import StateForKernel

from torch import Tensor

from typing_extensions import Tuple


class Kernel:
    def forward(
        self, state: StateForKernel
    ) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
        r"""
        Args:
            state (StateForKernel)

        Returns:
            k (Tensor): Kernel values $k(x_i, x_j)$, (..., n, n)
            k_xj (Tensor): Gradient of $k(x_i, x_j)$ with respect to $x_j$, (..., n, n, d)
            k_xi (Tensor): Gradient of $k(x_i, x_j)$ with respect to $x_i$, (..., n, n, d)
            tr_k_xj_xi (Tensor): Trace of $\nabla_{x_i} \nabla_{x_j} k(x_i, x_j)$, (..., n, n)
            score_t_k_xk_xi_k_xi (Tensor): $s(x_j)^\top \nabla_{x_i} \nabla_{x_k} k(x_i, x_k) \nabla_{x_i} k(x_i, x_j)$, (..., n, n, n)
            tr_k_xj_xi_t_k_xk_xi (Tensor): Trace of $\nabla_{x_i} \nabla_{x_j} k(x_i, x_j) \nabla_{x_i} \nabla_{x_k} k(x_i, x_k)$, (..., n, n, n)

        Notes:
            The leading dimensions denoted by `...` are batch dimensions and must be equal to the batch dimensions of `state.x`.
        """

        x = state.x

        k = None
        k_xj = None

        if state.f_k_compute_k_xi:
            k_xi = None

        if state.f_k_compute_tr_k_xj_xi:
            tr_k_xj_xi = None

        if state.f_k_compute_score_t_k_xk_xi_k_xi:
            score = state.score
            score_t_k_xk_xi_k_xi = None

        if state.f_k_compute_tr_k_xj_xi_t_k_xk_xi:
            tr_k_xj_xi_t_k_xk_xi = None

        if state.f_k_compute_v_t_k_xj_xi_grad_v_score:
            v = state.v
            grad_v_score = state.grad_v_score
            v_t_k_xj_xi_grad_v_score = None

        raise NotImplementedError()

        return (
            k,
            k_xj,
            k_xi,
            tr_k_xj_xi,
            score_t_k_xk_xi_k_xi,
            tr_k_xj_xi_t_k_xk_xi,
            v_t_k_xj_xi_grad_v_score,
        )
