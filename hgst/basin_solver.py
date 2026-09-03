import numpy as np

class LoopLM_BasinSolver:
    """
    Looped Language Model (LoopLM) latent state-space solver.
    """
    def __init__(self, latent_dim=8, max_loops=12, exit_tol=1e-5):
        self.latent_dim = latent_dim
        self.max_loops = max_loops
        self.exit_tol = exit_tol
        np.random.seed(42)
        W = np.random.randn(latent_dim, latent_dim) * 0.4
        self.W = (W - W.T)
        self.W_proj = np.eye(latent_dim) + 0.1 * self.W

    def recurrent_loop_step(self, h):
        return np.tanh(self.W_proj @ h)

    def solve_latent_trajectory(self, h_init):
        h = np.copy(h_init)
        trajectory = [h.copy()]
        for _ in range(self.max_loops):
            h_next = self.recurrent_loop_step(h)
            delta = np.linalg.norm(h_next - h)
            h = h_next
            trajectory.append(h.copy())
            if delta < self.exit_tol:
                break
        return h, trajectory, len(trajectory) - 1


class BasinUltimate:
    """
    Basin-Ultimate: Integrates LoopLM recurrent latent refinement with
    curvature-regularized Riemannian descent and exact Sheaf Laplacian verification.
    """
    def __init__(self, solver: LoopLM_BasinSolver):
        self.solver = solver

    def solve(self, z_init, grad_fn, hess_fn, sheaf_op, gamma=0.2, lambda_reg=2.0):
        h_refined, traj, loops = self.solver.solve_latent_trajectory(z_init)
        grad = grad_fn(h_refined)
        hess = hess_fn(h_refined)
        reg_hess_inv = np.linalg.inv(hess + lambda_reg * np.eye(len(h_refined)))
        z_minimized = h_refined - gamma * (reg_hess_inv @ grad)
        
        L_F = sheaf_op.T @ sheaf_op
        eigvals, eigvecs = np.linalg.eigh(L_F)
        null_mask = np.isclose(eigvals, 0.0, atol=1e-6)
        
        if np.any(null_mask):
            null_basis = eigvecs[:, null_mask]
            z_admissible = null_basis @ (null_basis.T @ z_minimized)
        else:
            z_admissible = z_minimized

        residual = float(np.linalg.norm(sheaf_op @ z_admissible))
        
        return {
            "z_final": z_admissible,
            "loops_used": loops,
            "sheaf_residual": residual,
            "is_admissible": residual < 1e-5
        }
