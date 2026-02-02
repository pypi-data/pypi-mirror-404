from svgd.kernels import Kernel
from svgd.kernels.parameters import KP
from svgd.states import StateForKernel

import torch
from torch import Tensor
from torch.nn import Module

from typing_extensions import Tuple


class RBFD(Kernel, Module):
    """
    RBF kernel with a vector kernel bandwidth: $k(x, y) = \\exp( -\\sum_d \\frac{(x_d - y_d)^2}{2\\sigma_d^2} )$
    """
    def __init__(self, sigma: KP):
        """
        Args:
            sigma (KP): Kernel bandwidth
        """

        Module.__init__(self)
        self.sigma = sigma

    def forward(
        self, state: StateForKernel
    ) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
        x = state.x

        outer_difference = x.unsqueeze(-2).sub(x.unsqueeze(-3))

        sigma = self.sigma.forward(state)

        if sigma.shape[-1] != x.shape[-1]:
            raise Exception("sigma must be a d-dimensional vector")

        gamma = sigma.pow(2).mul(2).add(1e-8).pow(-1)
        gamma_outer_difference = gamma.unsqueeze(-2).unsqueeze(-2).mul(outer_difference)
        gamma_outer_difference_squared = gamma_outer_difference.pow(2)

        k = (
            gamma.unsqueeze(-2)
            .unsqueeze(-2)
            .mul(outer_difference.pow(2))
            .sum(-1)
            .mul(-1)
            .exp()
        )
        k_xj = k.unsqueeze(-1).mul(gamma_outer_difference).mul(2)

        k_xi = torch.empty(0)
        tr_k_xj_xi = torch.empty(0)
        score_t_k_xk_xi_k_xi = torch.empty(0)
        tr_k_xj_xi_t_k_xk_xi = torch.empty(0)
        v_t_k_xj_xi_grad_v_score = torch.empty(0)

        if state.f_k_compute_k_xi:
            k_xi = k_xj.mul(-1)

        if state.f_k_compute_tr_k_xj_xi:
            tr_k_xj_xi = (
                gamma_outer_difference_squared.sum(-1)
                .mul(-2)
                .add(gamma.sum(-1).unsqueeze(-1).unsqueeze(-1))
                .mul(k)
                .mul(2)
            )

        if state.f_k_compute_score_t_k_xk_xi_k_xi:
            score = state.score
            score_gamma = score.mul(gamma.unsqueeze(-2))
            score_t_k_xk_xi_k_xi = (
                score_gamma.unsqueeze(-3)
                .matmul(outer_difference.transpose(-2, -1))
                .mul(
                    k_xi.mul(gamma.unsqueeze(-2).unsqueeze(-2)).matmul(
                        outer_difference.transpose(-2, -1)
                    )
                )
                .mul(-2)
                .add(score_gamma.unsqueeze(-3).mul(k_xi).sum(-1).unsqueeze(-1))
                .mul(k.unsqueeze(-2))
                .mul(2)
            )

        if state.f_k_compute_tr_k_xj_xi_t_k_xk_xi:
            tr_k_xj_xi_t_k_xk_xi_1 = (
                gamma_outer_difference.matmul(gamma_outer_difference.transpose(-2, -1))
                .pow(2)
                .mul(4)
            )
            tr_k_xj_xi_t_k_xk_xi_2_1 = (
                gamma.unsqueeze(-2)
                .unsqueeze(-2)
                .mul(gamma_outer_difference_squared)
                .sum(-1)
            )
            tr_k_xj_xi_t_k_xk_xi_2 = (
                tr_k_xj_xi_t_k_xk_xi_2_1.unsqueeze(-1)
                .add(tr_k_xj_xi_t_k_xk_xi_2_1.unsqueeze(-2))
                .mul(-2)
            )
            tr_k_xj_xi_t_k_xk_xi_3 = (
                gamma.pow(2).sum(-1).unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
            )
            tr_k_xj_xi_t_k_xk_xi = (
                tr_k_xj_xi_t_k_xk_xi_1.add(tr_k_xj_xi_t_k_xk_xi_2)
                .add(tr_k_xj_xi_t_k_xk_xi_3)
                .mul(k.unsqueeze(-1))
                .mul(k.unsqueeze(-2))
                .mul(4)
            )

        if state.f_k_compute_v_t_k_xj_xi_grad_v_score:
            v = state.v
            grad_v_score = state.grad_v_score
            v_t_k_xj_xi_grad_v_score = (
                v.unsqueeze(-2)
                .mul(gamma_outer_difference)
                .sum(-1)
                .mul(grad_v_score.unsqueeze(-2).mul(gamma_outer_difference).sum(-1))
                .mul(-2)
                .add(gamma.unsqueeze(-2).mul(v).mul(grad_v_score).sum(-1).unsqueeze(-1))
                .mul(k)
                .mul(2)
            )

        return (
            k,
            k_xj,
            k_xi,
            tr_k_xj_xi,
            score_t_k_xk_xi_k_xi,
            tr_k_xj_xi_t_k_xk_xi,
            v_t_k_xj_xi_grad_v_score,
        )
