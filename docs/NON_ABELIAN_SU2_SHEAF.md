# Non-Abelian SU(2) Gauge-Sheaf and Octahedral Quantum CSS Homology Code

This module extends the HGST framework to non-Abelian $SU(2)$ Yang-Mills gauge sheaves defined on an octahedral 2-sphere cell complex ($S^2 \cong \partial \Delta_{\text{oct}}$).

## Mathematical Overview

1. **Non-Abelian Gauge Sheaf**:
   Vertex/edge stalks $\mathcal{F}(v) \cong \mathbb{C}^2$ with non-commutative parallel transport $U_{uv} \in SU(2)$.
   When holonomy flux around all faces vanishes ($W_{\partial f} = I_2$), the Laplacian kernel matches the stalk dimension:
   $$\operatorname{nullity}(L_{\mathcal{F}}) = 2$$

2. **Octahedral CSS Stabilizers**:
   Constructed from topological boundary operators $\partial_2 \in \mathbb{F}_2^{12 \times 8}$ and $\partial_1 \in \mathbb{F}_2^{6 \times 12}$:
   $$H_X H_Z^\top = \partial_1 \partial_2 \equiv \mathbf{0} \pmod 2$$
