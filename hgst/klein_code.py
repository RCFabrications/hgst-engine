import numpy as np

class KleinBottleQuantumCode:
    """
    [[27, 2, d]] Topological Quantum CSS Code on a Klein Bottle.
    """
    def __init__(self):
        self.build_triangulation()

    def build_triangulation(self):
        triangles = []
        for r in range(3):
            for c in range(3):
                v00 = r * 3 + c
                v01 = r * 3 + ((c + 1) % 3)
                if r < 2:
                    v10 = (r + 1) * 3 + c
                    v11 = (r + 1) * 3 + ((c + 1) % 3)
                else:
                    v10 = 0 * 3 + ((3 - c) % 3)
                    v11 = 0 * 3 + ((3 - (c + 1)) % 3)
                triangles.append((v00, v01, v11))
                triangles.append((v00, v11, v10))
                
        edges_set = set()
        for (v0, v1, v2) in triangles:
            for (u, v) in [(v0, v1), (v1, v2), (v2, v0)]:
                edges_set.add(tuple(sorted((u, v))))
        self.edges = sorted(list(edges_set))
        self.triangles = triangles
        self.edge_map = {e: i for i, e in enumerate(self.edges)}
        
        self.d1 = np.zeros((9, len(self.edges)), dtype=int)
        for e_idx, (u, v) in enumerate(self.edges):
            self.d1[u, e_idx] = 1
            self.d1[v, e_idx] = 1
            
        self.d2 = np.zeros((len(self.edges), len(self.triangles)), dtype=int)
        for t_idx, (v0, v1, v2) in enumerate(self.triangles):
            for (u, v) in [(v0, v1), (v1, v2), (v2, v0)]:
                e = self.edge_map[tuple(sorted((u, v)))]
                self.d2[e, t_idx] = 1

    def get_css_stabilizers(self):
        Hx = self.d1 % 2
        Hz = self.d2.T % 2
        commutation = (Hx @ Hz.T) % 2
        return Hx, Hz, commutation
