/*
 * hgst_opportunity_engine.c
 * Native SIMD C Kernel for In-Process Opportunity Scanning & Direct Kernel Actuation.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define LATENT_DIM 512
#define MAX_TARGET_RADIUS 2.85

typedef struct {
    uint64_t pmu_cycles;
    uint64_t l3_cache_misses;
    uint64_t ap_queue_depth;
    uint64_t memory_bandwidth_mbps;
    double   synthetic_hw_noise;
} kernel_live_state_t;

typedef struct {
    uint64_t step;
    double   energy_barrier;
    double   associator_curvature;
    uint8_t  transition_type;
    uint8_t  executed;
    uint8_t  reserved[6];
} opportunity_event_t;

static const int8_t CD_SIGNS[16][16] = {
    { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
    { 1,-1, 1,-1, 1,-1,-1, 1, 1,-1,-1, 1,-1, 1, 1,-1},
    { 1,-1,-1, 1, 1, 1,-1,-1, 1, 1,-1,-1, 1,-1, 1,-1},
    { 1, 1,-1,-1, 1,-1, 1,-1, 1,-1, 1,-1,-1, 1,-1,-1},
    { 1,-1,-1,-1,-1, 1, 1, 1, 1, 1, 1,-1,-1,-1,-1, 1},
    { 1, 1,-1, 1,-1,-1,-1, 1, 1,-1, 1, 1,-1,-1, 1,-1},
    { 1, 1, 1,-1,-1, 1,-1,-1, 1,-1,-1,-1, 1, 1,-1, 1},
    { 1,-1, 1, 1,-1,-1, 1,-1, 1, 1,-1, 1, 1,-1,-1,-1},
    { 1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 1, 1, 1, 1, 1, 1},
    { 1, 1,-1, 1,-1, 1, 1,-1,-1,-1,-1, 1,-1, 1, 1,-1},
    { 1, 1, 1,-1,-1,-1, 1, 1,-1, 1,-1,-1, 1,-1, 1,-1},
    { 1,-1, 1,-1, 1,-1,-1,-1,-1,-1, 1,-1,-1, 1,-1, 1},
    { 1, 1,-1, 1, 1, 1,-1,-1,-1, 1,-1, 1,-1,-1,-1, 1},
    { 1,-1, 1,-1, 1, 1,-1, 1,-1,-1, 1,-1, 1,-1,-1,-1},
    { 1,-1,-1, 1, 1,-1, 1, 1,-1,-1,-1, 1, 1, 1,-1,-1},
    { 1, 1, 1, 1,-1, 1,-1, 1,-1, 1,-1,-1,-1, 1, 1,-1}
};

static const uint8_t CD_INDEX[16][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    { 1, 0, 3, 2, 5, 4, 7, 6, 9, 8,11,10,13,12,15,14},
    { 2, 3, 0, 1, 6, 7, 4, 5,10,11, 8, 9,14,15,12,13},
    { 3, 2, 1, 0, 7, 6, 5, 4,11,10, 9, 8,15,14,13,12},
    { 4, 5, 6, 7, 0, 1, 2, 3,12,13,14,15, 8, 9,10,11},
    { 5, 4, 7, 6, 1, 0, 3, 2,13,12,15,14, 9, 8,11,10},
    { 6, 7, 4, 5, 2, 3, 0, 1,14,15,12,13,10,11, 8, 9},
    { 7, 6, 5, 4, 3, 2, 1, 0,15,14,13,12,11,10, 9, 8},
    { 8, 9,10,11,12,13,14,15, 0, 1, 2, 3, 4, 5, 6, 7},
    { 9, 8,11,10,13,12,15,14, 1, 0, 3, 2, 5, 4, 7, 6},
    {10,11, 8, 9,14,15,12,13, 2, 3, 0, 1, 6, 7, 4, 5},
    {11,10, 9, 8,15,14,13,12, 3, 2, 1, 0, 7, 6, 5, 4},
    {12,13,14,15, 8, 9,10,11, 4, 5, 6, 7, 0, 1, 2, 3},
    {13,12,15,14, 9, 8,11,10, 5, 4, 7, 6, 1, 0, 3, 2},
    {14,15,12,13,10,11, 8, 9, 6, 7, 4, 5, 2, 3, 0, 1},
    {15,14,13,12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0}
};

void sedenion_mul_raw(const double *a, const double *b, double *out) {
    memset(out, 0, sizeof(double) * 16);
    for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
            uint8_t k = CD_INDEX[i][j];
            int8_t s = CD_SIGNS[i][j];
            out[k] += s * a[i] * b[j];
        }
    }
}

int execute_opportunity_cycle(
    double *latent_state,
    const kernel_live_state_t *kstate,
    opportunity_event_t *out_event,
    double *out_projected,
    double lambda_base
) {
    latent_state[0] = (double)(kstate->pmu_cycles % 1000) / 1000.0 * 0.1;
    latent_state[1] = (double)(kstate->l3_cache_misses % 100) / 100.0 * 0.1;
    latent_state[2] = (double)(kstate->ap_queue_depth % 32) / 32.0 * 0.1;
    latent_state[3] = (double)(kstate->memory_bandwidth_mbps % 10000) / 10000.0 * 0.1;

    double s_a[16], s_b[16], s_c[16];
    memcpy(s_a, latent_state, 16 * sizeof(double));
    for (int i = 0; i < 16; i++) {
        s_b[i] = latent_state[(i + 1) % 16];
        s_c[i] = latent_state[(i + 3) % 16];
    }

    double ab[16], bc[16], ab_c[16], a_bc[16];
    sedenion_mul_raw(s_a, s_b, ab);
    sedenion_mul_raw(s_b, s_c, bc);
    sedenion_mul_raw(ab, s_c, ab_c);
    sedenion_mul_raw(s_a, bc, a_bc);

    double curvature = 0.0;
    for (int i = 0; i < 16; i++) {
        double diff = ab_c[i] - a_bc[i];
        curvature += diff * diff;
    }
    curvature = sqrt(curvature);

    double energy_barrier = (curvature * 0.4) + (kstate->synthetic_hw_noise * 0.6);
    out_event->energy_barrier = energy_barrier;
    out_event->associator_curvature = curvature;

    if (energy_barrier < 0.15) {
        out_event->transition_type = 2; // Jump
        out_event->executed = 1;
        for (int i = 0; i < 16; i++) {
            latent_state[i] = ab_c[i] * 0.05;
        }
    } else if (curvature > 2.0) {
        out_event->transition_type = 3; // Fold
        out_event->executed = 1;
        for (int i = 0; i < LATENT_DIM / 2; i++) {
            double tmp = latent_state[i];
            latent_state[i] = latent_state[LATENT_DIM - 1 - i];
            latent_state[LATENT_DIM - 1 - i] = tmp;
        }
    } else {
        out_event->transition_type = 1; // Steer
        out_event->executed = 1;
    }

    double norm_sq = 0.0;
    double eff_lambda = lambda_base + 0.02 * tanh(curvature);
    for (int i = 0; i < LATENT_DIM; i += 2) {
        double q = latent_state[i];
        double p = (i + 1 < LATENT_DIM) ? latent_state[i+1] : 0.0;
        double q_new = q * cos(eff_lambda) - p * sin(eff_lambda);
        double p_new = q * sin(eff_lambda) + p * cos(eff_lambda);
        out_projected[i] = q_new;
        norm_sq += q_new * q_new;
        if (i + 1 < LATENT_DIM) {
            out_projected[i+1] = p_new;
            norm_sq += p_new * p_new;
        }
    }

    double norm = sqrt(norm_sq);
    if (norm > MAX_TARGET_RADIUS && norm > 1e-12) {
        double scale = MAX_TARGET_RADIUS / norm;
        for (int i = 0; i < LATENT_DIM; i++) {
            out_projected[i] *= scale;
        }
    }

    return (norm <= 3.0) ? 0 : -1;
}
