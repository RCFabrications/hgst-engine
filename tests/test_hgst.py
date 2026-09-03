import unittest
import numpy as np
from hgst.engine import HGSTEngine
from hgst.non_abelian import NonAbelianOctahedralEngine
from hgst.kinematics import TopologicalKinematicsEngine
from hgst.basin_solver import LoopLM_BasinSolver, BasinUltimate
from hgst.klein_code import KleinBottleQuantumCode
from hgst.octonionic import OctonionicG2Transceiver

class TestHGSTSuite(unittest.TestCase):
    def test_abelian_flux_cancellation(self):
        engine = HGSTEngine(num_nodes=4, stalk_dim=2)
        L, _ = engine.build_sheaf_laplacian([0.2, 0.5, -0.3, -0.4])
        eigvals = np.linalg.eigvalsh(L)
        self.assertTrue(np.isclose(eigvals[0], 0.0, atol=1e-8))

    def test_non_abelian_octahedral_kernel(self):
        engine = NonAbelianOctahedralEngine()
        vertex_gauges = [engine.su2_matrix([0, 0, 1], 0.1 * i) for i in range(6)]
        L, _ = engine.build_nonabelian_sheaf(vertex_gauges)
        eigvals = np.linalg.eigvalsh(L)
        nullity = int(np.sum(np.isclose(eigvals, 0.0, atol=1e-8)))
        self.assertEqual(nullity, 2)

    def test_css_orthogonality(self):
        engine = NonAbelianOctahedralEngine()
        Hx, Hz, commutation = engine.build_octahedral_css()
        self.assertTrue(np.all(commutation == 0))

    def test_kinematic_synchronization(self):
        engine = TopologicalKinematicsEngine()
        res = engine.evaluate_drivetrain([1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0])
        self.assertTrue(res["is_synchronous"])
        self.assertEqual(res["harmonic_modes"], 2)

    def test_klein_code_nilpotency(self):
        code = KleinBottleQuantumCode()
        Hx, Hz, comm = code.get_css_stabilizers()
        self.assertTrue(np.all(comm == 0))

    def test_octonionic_orthogonality(self):
        engine = OctonionicG2Transceiver()
        u = np.array([1, 0, 0, 0, 0, 0, 0, 0])
        L = engine.left_mult_matrix(u)
        self.assertTrue(np.allclose(L.T @ L, np.eye(8)))

    def test_looplm_basin_ultimate(self):
        solver = LoopLM_BasinSolver(latent_dim=4, max_loops=10)
        ultimate = BasinUltimate(solver)
        sheaf_op = np.array([[-1.0, 1.0, 0.0, 0.0], [0.0, -1.0, 1.0, 0.0], [0.0, 0.0, -1.0, 1.0], [1.0, 0.0, 0.0, -1.0]])
        res = ultimate.solve(np.array([1.0, 0.5, -0.2, 0.8]), lambda z: z, lambda z: np.eye(4), sheaf_op)
        self.assertTrue(res["is_admissible"])
        self.assertLess(res["sheaf_residual"], 1e-5)

if __name__ == "__main__":
    unittest.main()
