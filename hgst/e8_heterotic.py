import numpy as np

class E8HeteroticTransceiver:
    """
    E8 Exceptional Root Lattice & Gosset Polytope Transceiver.
    """
    def __init__(self):
        self.roots = self.build_240_roots()
        self.cartan = np.array([
            [ 2, -1,  0,  0,  0,  0,  0,  0],
            [-1,  2, -1,  0,  0,  0,  0,  0],
            [ 0, -1,  2, -1,  0,  0,  0,  0],
            [ 0,  0, -1,  2, -1,  0,  0,  0],
            [ 0,  0,  0, -1,  2, -1,  0, -1],
            [ 0,  0,  0,  0, -1,  2, -1,  0],
            [ 0,  0,  0,  0,  0, -1,  2,  0],
            [ 0,  0,  0,  0, -1,  0,  0,  2]
        ])

    def build_240_roots(self):
        roots = []
        for i in range(8):
            for j in range(i + 1, 8):
                for s1 in [-1.0, 1.0]:
                    for s2 in [-1.0, 1.0]:
                        r = np.zeros(8)
                        r[i] = s1; r[j] = s2
                        roots.append(r)
        for bits in range(256):
            signs = [1.0 if (bits & (1 << k)) else -1.0 for k in range(8)]
            if signs.count(-1.0) % 2 == 0:
                roots.append(np.array(signs) * 0.5)
        return np.array(roots)

    def build_e8_sheaf_laplacian(self, num_nodes=8):
        edges = [(i, (i + 1) % num_nodes) for i in range(num_nodes)]
        d = 8
        ne = len(edges)
        delta0 = np.zeros((ne * d, num_nodes * d))
        
        r = self.roots[0]
        W_refl = np.eye(8) - np.outer(r, r)
        
        for idx, (u, v) in enumerate(edges):
            delta0[idx*d:(idx+1)*d, u*d:(u+1)*d] = -np.eye(d)
            delta0[idx*d:(idx+1)*d, v*d:(v+1)*d] = W_refl if idx == 0 else np.eye(d)
            
        L_e8 = delta0.T @ delta0
        return L_e8
