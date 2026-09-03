import numpy as np

class OctonionicG2Transceiver:
    """
    Non-associative octonionic sheaf on the 24-cell polytope with G_2 gauge invariance.
    """
    def __init__(self):
        self.fano_triples = [
            (1, 2, 3), (1, 4, 5), (1, 7, 6),
            (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)
        ]
        self.build_mult_table()

    def build_mult_table(self):
        self.mult = np.zeros((8, 8, 8))
        for i in range(8):
            self.mult[0, i, i] = 1.0
            self.mult[i, 0, i] = 1.0
            if i > 0:
                self.mult[i, i, 0] = -1.0
        for (a, b, c) in self.fano_triples:
            self.mult[a, b, c] = 1.0;  self.mult[b, a, c] = -1.0
            self.mult[b, c, a] = 1.0;  self.mult[c, b, a] = -1.0
            self.mult[c, a, b] = 1.0;  self.mult[a, c, b] = -1.0

    def left_mult_matrix(self, oct_vec):
        v = oct_vec / np.linalg.norm(oct_vec)
        L = np.zeros((8, 8))
        for i in range(8):
            for j in range(8):
                for k in range(8):
                    L[k, j] += v[i] * self.mult[i, j, k]
        return L
