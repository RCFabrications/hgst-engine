import numpy as np
import scipy.linalg as la

class NonAbelianOctahedralEngine:
    """
    Non-Abelian SU(2) gauge sheaf and CSS stabilizer engine on an Octahedron.
    """
    def __init__(self):
        self.edges = [
            (0, 2), (2, 1), (1, 3), (3, 0),
            (0, 4), (2, 4), (1, 4), (3, 4),
            (0, 5), (2, 5), (1, 5), (3, 5)
        ]
        self.faces = [
            [0, 5, 4], [1, 6, 5], [2, 7, 6], [3, 4, 7],
            [0, 9, 8], [1, 10, 9], [2, 11, 10], [3, 8, 11]
        ]
        self.sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        self.sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

    def su2_matrix(self, axis, angle):
        axis = np.asarray(axis, dtype=float)
        axis = axis / np.linalg.norm(axis)
        gen = axis[0]*self.sigma_x + axis[1]*self.sigma_y + axis[2]*self.sigma_z
        return la.expm(-1j * (angle / 2.0) * gen)

    def build_nonabelian_sheaf(self, vertex_gauges):
        d = 2
        nv = 6
        ne = len(self.edges)
        delta0 = np.zeros((ne * d, nv * d), dtype=complex)
        for idx, (u, v) in enumerate(self.edges):
            U_uv = vertex_gauges[u] @ vertex_gauges[v].conj().T
            delta0[idx*d:(idx+1)*d, u*d:(u+1)*d] = -np.eye(d, dtype=complex)
            delta0[idx*d:(idx+1)*d, v*d:(v+1)*d] = U_uv
        L_F = delta0.conj().T @ delta0
        return L_F, delta0

    def build_octahedral_css(self):
        d2 = np.zeros((12, 8), dtype=int)
        for f_idx, face_edges in enumerate(self.faces):
            for e in face_edges:
                d2[e, f_idx] = 1
        d1 = np.zeros((6, 12), dtype=int)
        for e_idx, (u, v) in enumerate(self.edges):
            d1[u, e_idx] = 1
            d1[v, e_idx] = 1
        Hx = d1 % 2
        Hz = d2.T % 2
        commutation = (Hx @ Hz.T) % 2
        return Hx, Hz, commutation
