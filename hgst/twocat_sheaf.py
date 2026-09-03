import numpy as np

class TwoCategorySheafMonad:
    """
    2-Category Sheaf & Beilinson Monad Transceiver.
    """
    def __init__(self, k_instanton=2, r_rank=2):
        self.k = k_instanton
        self.r = r_rank
        self.dim_E0 = self.k
        self.dim_E1 = self.r + 2 * self.k
        self.dim_E2 = self.k

    def construct_beilinson_monad(self):
        alpha = np.zeros((self.dim_E1, self.dim_E0), dtype=complex)
        alpha[:self.k, :] = np.eye(self.k)
        
        beta = np.zeros((self.dim_E2, self.dim_E1), dtype=complex)
        beta[:, self.k + self.r:] = np.eye(self.k)
        
        nilpotent = bool(np.allclose(beta @ alpha, 0.0))
        dim_coh = (self.dim_E1 - self.dim_E2) - self.dim_E0
        return alpha, beta, nilpotent, dim_coh

    def construct_higher_1_laplacian(self):
        edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        triangles = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
        d = self.r
        
        delta0 = np.zeros((len(edges) * d, 4 * d))
        for idx, (u, v) in enumerate(edges):
            delta0[idx*d:(idx+1)*d, u*d:(u+1)*d] = -np.eye(d)
            delta0[idx*d:(idx+1)*d, v*d:(v+1)*d] = np.eye(d)
            
        delta1 = np.zeros((len(triangles) * d, len(edges) * d))
        for t_idx, (u, v, w) in enumerate(triangles):
            e_uv = edges.index((u, v))
            e_vw = edges.index((v, w))
            e_uw = edges.index((u, w))
            delta1[t_idx*d:(t_idx+1)*d, e_vw*d:(e_vw+1)*d] += np.eye(d)
            delta1[t_idx*d:(t_idx+1)*d, e_uw*d:(e_uw+1)*d] -= np.eye(d)
            delta1[t_idx*d:(t_idx+1)*d, e_uv*d:(e_uv+1)*d] += np.eye(d)
            
        coboundary_zero = bool(np.allclose(delta1 @ delta0, 0.0))
        L1 = delta0 @ delta0.T + delta1.T @ delta1
        nullity_L1 = int(np.sum(np.isclose(np.linalg.eigvalsh(L1), 0.0, atol=1e-5)))
        return coboundary_zero, L1, nullity_L1
