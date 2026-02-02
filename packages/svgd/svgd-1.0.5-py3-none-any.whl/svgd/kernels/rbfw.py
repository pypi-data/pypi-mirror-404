from svgd.kernels import Kernel
from svgd.kernels.parameters import KP
from svgd.states import StateForKernel

import torch
from torch import Tensor
from torch.nn import Module

from typing_extensions import Tuple


class RBFW(Kernel, Module):
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
        outer_difference_squared = outer_difference.pow(2)

        sigma = self.sigma.forward(state)
        gamma = sigma.pow(2).add(1e-8).pow(-1)
        gamma_outer_difference_squared = (
            gamma.unsqueeze(-2).unsqueeze(-2).mul(outer_difference_squared)
        )

        k_d = gamma_outer_difference_squared.div(-2).exp()
        k = k_d.mean(-1)
        k_xj = (
            gamma.unsqueeze(-2)
            .unsqueeze(-2)
            .mul(k_d)
            .mul(outer_difference)
            .div(x.shape[-1])
        )

        k_xi = torch.empty(0)
        tr_k_xj_xi = torch.empty(0)
        score_t_k_xk_xi_k_xi = torch.empty(0)
        tr_k_xj_xi_t_k_xk_xi = torch.empty(0)
        v_t_k_xj_xi_grad_v_score = torch.empty(0)

        if state.f_k_compute_k_xi:
            k_xi = k_xj.mul(-1)

        if state.f_k_compute_tr_k_xj_xi:
            tr_k_xj_xi = (
                gamma_outer_difference_squared.mul(-1)
                .add(1)
                .mul(k_d)
                .mul(gamma.unsqueeze(-2).unsqueeze(-2))
                .mean(-1)
            )

        if state.f_k_compute_score_t_k_xk_xi_k_xi:
            score = state.score
            score_t_k_xk_xi_k_xi = (
                gamma
                .unsqueeze(-2)
                .unsqueeze(-2)
                .mul(outer_difference_squared).mul(-1)
                .add(1)
                .mul(score.unsqueeze(-3))
                .mul(k_xi)
                .mul(gamma.unsqueeze(-2).unsqueeze(-2))
                .matmul(k_d.transpose(-2, -1))
                .div(x.shape[-1])
            )

        if state.f_k_compute_tr_k_xj_xi_t_k_xk_xi:
            tr_k_xj_xi_t_k_xk_xi_1 = (
                outer_difference.matmul(outer_difference.transpose(-2, -1))
                .pow(2)
                .mul(gamma.pow(2).unsqueeze(-1).unsqueeze(-1).unsqueeze(-1))
                .mul(4)
            )
            tr_k_xj_xi_t_k_xk_xi_2 = (
                squared_distance.unsqueeze(-1)
                .add(squared_distance.unsqueeze(-2))
                .mul(gamma.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1))
                .mul(-2)
            )
            tr_k_xj_xi_t_k_xk_xi = (
                tr_k_xj_xi_t_k_xk_xi_1.add(tr_k_xj_xi_t_k_xk_xi_2)
                .add(x.shape[-1])
                .mul(k.unsqueeze(-1))
                .mul(k.unsqueeze(-2))
                .mul(gamma.pow(2).unsqueeze(-1).unsqueeze(-1).unsqueeze(-1))
                .mul(4)
            )

        if state.f_k_compute_v_t_k_xj_xi_grad_v_score:
            v = state.v
            grad_v_score = state.grad_v_score
            v_t_k_xj_xi_grad_v_score = (
                v.unsqueeze(-2)
                .mul(outer_difference)
                .sum(-1)
                .mul(grad_v_score.unsqueeze(-2).mul(outer_difference).sum(-1))
                .mul(gamma.unsqueeze(-1).unsqueeze(-1))
                .mul(-2)
                .add(v.mul(grad_v_score).sum(-1).unsqueeze(-1))
                .mul(k)
                .mul(gamma.unsqueeze(-1).unsqueeze(-1))
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
