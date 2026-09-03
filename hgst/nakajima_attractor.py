import numpy as np

class NakajimaHyperKahlerAttractor:
    """
    ADHM Quiver Instanton Moduli & BPS Horizon Attractor Engine.
    """
    def __init__(self, dim_v=2, dim_w=2, zeta=1.5):
        self.v = dim_v
        self.w = dim_w
        self.zeta = zeta

    def generate_adhm_configuration(self):
        np.random.seed(42)
        B1 = np.diag(np.random.randn(self.v) + 1j * np.random.randn(self.v))
        B2 = np.diag(np.random.randn(self.v) + 1j * np.random.randn(self.v))
        J = np.zeros((self.w, self.v), dtype=complex)
        I = np.sqrt(self.zeta) * np.eye(self.v, self.w, dtype=complex)
        return B1, B2, I, J

    def verify_moment_maps(self, B1, B2, I, J):
        mu_C = (B1 @ B2 - B2 @ B1) + I @ J
        mu_R = (B1 @ B1.conj().T - B1.conj().T @ B1) + \
               (B2 @ B2.conj().T - B2.conj().T @ B2) + \
               I @ I.conj().T - J.conj().T @ J
        return float(np.linalg.norm(mu_C)), float(np.linalg.norm(mu_R - self.zeta * np.eye(self.v)))

    def compute_bps_attractor_fixed_point(self, p_charge=4.0, q_charge=9.0):
        t_hor = np.sqrt(q_charge / p_charge)
        Z_hor = (p_charge * (t_hor**2) + q_charge) / (2.0 * t_hor)
        entropy_BH = np.pi * (Z_hor**2)
        return float(t_hor), float(Z_hor), float(entropy_BH)
