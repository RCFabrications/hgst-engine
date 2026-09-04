"""
orthogonal_attention_filter.py
Production Python Integration: Reverse Attention-Head Vector Projection Hook.
"""

import torch
import torch.nn as nn
from typing import Tuple

class OrthogonalSteeringHook:
    def __init__(self, d_model: int, d_head: int, target_direction: torch.Tensor):
        super().__init__()
        self.d_model = d_model
        self.d_head = d_head
        self.v = target_direction / torch.norm(target_direction)
        self.P_perp = torch.eye(d_model) - torch.outer(self.v, self.v)

    def pull_back_to_head_space(self, W_O: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        u_raw = torch.matmul(W_O, self.v)
        u_norm = torch.norm(u_raw)
        if u_norm > 1e-12:
            u_head = u_raw / u_norm
        else:
            u_head = u_raw
        P_head_perp = torch.eye(self.d_head) - torch.outer(u_head, u_head)
        return u_head, P_head_perp

    def forward_hook(self, module: nn.Module, input_tensor: Tuple[torch.Tensor], output_tensor: torch.Tensor) -> torch.Tensor:
        device = output_tensor.device
        P_perp = self.P_perp.to(device)
        return torch.matmul(output_tensor, P_perp)
