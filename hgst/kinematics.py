import numpy as np
import scipy.linalg as la

class TopologicalKinematicsEngine:
    """
    Evaluates kinematic loop constraints and mesh boundary cycles via SU(2) sheaf cohomology.
    """
    def __init__(self, num_shafts=4):
        self.num_shafts = num_shafts
        self.edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        self.sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
        
    def evaluate_drivetrain(self, gear_ratios, backlash_angles):
        nv = self.num_shafts
        ne = len(self.edges)
        dim = 2
        delta0 = np.zeros((ne * dim, nv * dim), dtype=complex)
        holonomy = np.eye(2, dtype=complex)
        
        for idx, (u, v) in enumerate(self.edges):
            theta = 4.0 * np.arctan(gear_ratios[idx]) + backlash_angles[idx]
            U = la.expm(-1j * (theta / 2.0) * self.sigma_z)
            holonomy = holonomy @ U
            delta0[idx*dim:(idx+1)*dim, u*dim:(u+1)*dim] = -np.eye(dim, dtype=complex)
            delta0[idx*dim:(idx+1)*dim, v*dim:(v+1)*dim] = U
            
        L_M = delta0.conj().T @ delta0
        eigvals = np.linalg.eigvalsh(L_M)
        nullity = int(np.sum(np.isclose(eigvals, 0.0, atol=1e-8)))
        
        return {
            "holonomy_trace": float(np.real(np.trace(holonomy))),
            "is_synchronous": nullity == 2,
            "harmonic_modes": nullity
        }

    def validate_boundary_loop(self, boundary_segments):
        net_angle = sum(seg.get("turning_angle", 0.0) for seg in boundary_segments)
        is_closed = np.isclose(net_angle % (2 * np.pi), 0.0, atol=1e-4)
        return {
            "net_turning_angle": net_angle,
            "is_topologically_closed": bool(is_closed)
        }
