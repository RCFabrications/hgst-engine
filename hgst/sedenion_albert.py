import numpy as np

def cd_multiply(x, y, dim=16):
    if dim == 1:
        return np.array([x[0] * y[0]])
    half = dim // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    c_conj = c.copy(); c_conj[1:] = -c_conj[1:]
    d_conj = d.copy(); d_conj[1:] = -d_conj[1:]
    
    ac = cd_multiply(a, c, half)
    d_conj_b = cd_multiply(d_conj, b, half)
    da = cd_multiply(d, a, half)
    b_c_conj = cd_multiply(b, c_conj, half)
    
    res = np.zeros(dim)
    res[:half] = ac - d_conj_b
    res[half:] = da + b_c_conj
    return res

class SedenionAlbertTransceiver:
    def __init__(self):
        self.dim = 16
        
    def evaluate_freudenthal_cubic(self, r1, r2, r3, x, y, z):
        norm_x_sq = np.sum(x**2)
        norm_y_sq = np.sum(y**2)
        norm_z_sq = np.sum(z**2)
        xz = cd_multiply(x, z, 8)
        xzy = cd_multiply(xz, y, 8)
        return r1*r2*r3 - r1*norm_z_sq - r2*norm_y_sq - r3*norm_x_sq + 2.0*xzy[0]

    def build_zero_divisor_laplacian(self):
        dim_stalk = 16
        num_nodes = 4
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]
        delta_zd = np.zeros((len(edges) * dim_stalk, num_nodes * dim_stalk))
        
        e_zd = np.zeros(16); e_zd[1] = 1.0; e_zd[10] = 1.0
        M_zd = np.zeros((16, 16))
        for col in range(16):
            b = np.zeros(16); b[col] = 1.0
            M_zd[:, col] = cd_multiply(e_zd, b, 16)
            
        for idx, (u, v) in enumerate(edges):
            delta_zd[idx*dim_stalk:(idx+1)*dim_stalk, u*dim_stalk:(u+1)*dim_stalk] = -np.eye(dim_stalk)
            delta_zd[idx*dim_stalk:(idx+1)*dim_stalk, v*dim_stalk:(v+1)*dim_stalk] = np.linalg.qr(M_zd + np.eye(16))[0]
            
        return delta_zd.T @ delta_zd
