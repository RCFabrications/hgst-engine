/*
 * hgst_static_weight_baker.h
 *
 * Production Header: In-Place Static Weight-Baking via Reverse Attention Head Pullback.
 * Modifies Transformer W_O projection tensors directly in memory/disk to eliminate
 * target behavioural vectors with 0 runtime overhead.
 */

#ifndef HGST_STATIC_WEIGHT_BAKER_H
#define HGST_STATIC_WEIGHT_BAKER_H

#include <stdint.h>
#include <string.h>
#include <math.h>

/**
 * Applies surgical orthogonal nullification in-place to the output weight matrix W_O.
 * 
 * @param W_O          Pointer to head projection matrix [d_head * d_model].
 * @param target_v     Target direction vector in residual stream [d_model].
 * @param d_head       Attention head dimension (e.g., 64, 128).
 * @param d_model      Residual stream dimension (e.g., 4096, 8192).
 */
static inline void hgst_bake_head_weights_inplace(
    double *W_O,
    const double *target_v,
    uint32_t d_head,
    uint32_t d_model
) {
    // 1. Compute unit vector v_hat
    double v_norm = 0.0;
    for (uint32_t i = 0; i < d_model; i++) {
        v_norm += target_v[i] * target_v[i];
    }
    v_norm = sqrt(v_norm);
    if (v_norm < 1e-12) return;

    // 2. Direct Left-Pullback: u = W_O * v_hat
    double u[d_head];
    memset(u, 0, sizeof(double) * d_head);
    double u_norm = 0.0;

    for (uint32_t i = 0; i < d_head; i++) {
        for (uint32_t j = 0; j < d_model; j++) {
            u[i] += W_O[i * d_model + j] * (target_v[j] / v_norm);
        }
        u_norm += u[i] * u[i];
    }
    u_norm = sqrt(u_norm);
    if (u_norm < 1e-12) return; // Head does not write into target_v

    for (uint32_t i = 0; i < d_head; i++) {
        u[i] /= u_norm;
    }

    // 3. Bake Orthogonal Projector In-Place: W_O = (I - u u^T) * W_O
    // For each column k: W_O[i][k] = W_O[i][k] - u[i] * sum_j(u[j] * W_O[j][k])
    for (uint32_t k = 0; k < d_model; k++) {
        double u_dot_col = 0.0;
        for (uint32_t j = 0; j < d_head; j++) {
            u_dot_col += u[j] * W_O[j * d_model + k];
        }
        for (uint32_t i = 0; i < d_head; i++) {
            W_O[i * d_model + k] -= u[i] * u_dot_col;
        }
    }
}

#endif // HGST_STATIC_WEIGHT_BAKER_H
