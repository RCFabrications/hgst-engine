import numpy as np

class HGSTEngine:
    """
    Homological Gauge-Stabilizer Transceiver implementation.
    """
    def __init__(self, num_nodes=4, stalk_dim=2):
        self.num_nodes = num_nodes
        self.stalk_dim = stalk_dim
        self.edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        
    def build_sheaf_laplacian(self, gauge_angles):
        ne = len(self.edges)
        d = self.stalk_dim
        delta0 = np.zeros((ne * d, self.num_nodes * d))
        for idx, (u, v) in enumerate(self.edges):
            th = gauge_angles[idx]
            R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            delta0[idx*d:(idx+1)*d, u*d:(u+1)*d] = -np.eye(d)
            delta0[idx*d:(idx+1)*d, v*d:(v+1)*d] = R
        L_F = delta0.T @ delta0
        return L_F, delta0

    def harmonic_projection(self, x, L_F):
        eigvals, eigvecs = np.linalg.eigh(L_F)
        null_mask = np.isclose(eigvals, 0.0, atol=1e-8)
        if not np.any(null_mask):
            return np.zeros_like(x)
        null_basis = eigvecs[:, null_mask]
        return null_basis @ (null_basis.T @ x)

    def generate_css_code(self):
        d2 = np.array([[1], [1], [1], [1]], dtype=int)
        d1 = np.array([
            [1, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1]
        ], dtype=int)
        Hx = d1 % 2
        Hz = d2.T % 2
        commutation = (Hx @ Hz.T) % 2
        return Hx, Hz, commutation
