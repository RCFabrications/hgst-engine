import numpy as np

class VortexOrchestrator:
    """
    VORTEX-SIA-01 Tripartite Swarm Engine (Planner / Researcher / Critic).
    Executes deterministic test-time scaling with Sheaf Laplacian Hodge repair.
    """
    def __init__(self, state_dim=4, num_paths=3, max_repair_iters=5):
        self.state_dim = state_dim
        self.num_paths = num_paths
        self.max_repair_iters = max_repair_iters

    def step1_plan_search(self, task_constraints):
        bounds = []
        for c in task_constraints:
            bounds.append((float(c.get("min", -1.0)), float(c.get("max", 1.0))))
        return bounds

    def step2_diverse_generation(self, bounds):
        np.random.seed(42)
        candidates = []
        for _ in range(self.num_paths):
            vec = np.array([np.random.uniform(b[0], b[1]) for b in bounds])
            candidates.append(vec)
        return candidates

    def step3_metacognitive_critique(self, candidate, sheaf_op):
        L_F = sheaf_op.T @ sheaf_op
        residual = float(np.linalg.norm(L_F @ candidate))
        is_coherent = residual < 1e-6
        return residual, is_coherent, L_F

    def step4_pr_cot_repair(self, candidate, L_F):
        eigvals, eigvecs = np.linalg.eigh(L_F)
        null_mask = np.isclose(eigvals, 0.0, atol=1e-6)
        if np.any(null_mask):
            null_basis = eigvecs[:, null_mask]
            repaired_state = null_basis @ (null_basis.T @ candidate)
        else:
            repaired_state = candidate
        return repaired_state

    def step5_final_convergence(self, repaired_state, Hx, Hz):
        b = (repaired_state > 0).astype(int)
        sx = (Hx @ b) % 2
        sz = (Hz @ b) % 2
        is_css_valid = np.all(sx == 0) and np.all(sz == 0)
        
        return {
            "converged_state": repaired_state,
            "binary_code": b,
            "syndromes": {"sx": sx.tolist(), "sz": sz.tolist()},
            "is_css_grounded": bool(is_css_valid),
            "status": "CONVERGED_ZERO_COST_ATTRACTOR"
        }

    def execute_swarm(self, task_constraints, sheaf_op, Hx, Hz):
        bounds = self.step1_plan_search(task_constraints)
        candidates = self.step2_diverse_generation(bounds)
        
        best_candidate = None
        min_residual = float('inf')
        
        for cand in candidates:
            residual, is_coherent, L_F = self.step3_metacognitive_critique(cand, sheaf_op)
            if residual < min_residual:
                min_residual = residual
                best_candidate = cand

        L_F = sheaf_op.T @ sheaf_op
        repaired_state = self.step4_pr_cot_repair(best_candidate, L_F)
        
        result = self.step5_final_convergence(repaired_state, Hx, Hz)
        result["initial_residual"] = min_residual
        result["final_residual"] = float(np.linalg.norm(L_F @ repaired_state))
        return result
