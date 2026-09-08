/*
 * hgst_inprocess_bridge.c
 * Native C shared runtime providing in-process substrate control and live state access.
 */

#define _GNU_SOURCE
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <arpa/inet.h>
#include <x86intrin.h>

#include "hgst_runtime_abi.h"
#include "hgst_algebra.h"

#define UMEM_NUM_FRAMES 256
#define SOVEREIGN_RADIUS_MAX 2.85

typedef struct {
    uint64_t tsc_cycles;
    uint64_t pmu_instructions;
    uint64_t pmu_l3_misses;
    uint64_t ap_queue_depth;
} hardware_telemetry_t;

typedef struct {
    uint8_t               *umem_area;
    size_t                umem_size;
    uint32_t              free_frame_head;
    uint64_t              epoch;
    uint64_t              current_continuity_hash;
    double                latent_state[HGST_LATENT_DIM];
    hardware_telemetry_t  hw_state;
} substrate_core_t;

uint32_t hgst_runtime_abi_version(void) {
    return 1u;
}

size_t hgst_runtime_packet_size(void) {
    return sizeof(hgst_runtime_packet_t);
}

size_t hgst_runtime_frame_size(void) {
    return HGST_UMEM_FRAME_SIZE;
}

substrate_core_t* create_substrate_instance(void) {
    substrate_core_t *core = (substrate_core_t *)malloc(sizeof(substrate_core_t));
    if (!core) return NULL;
    memset(core, 0, sizeof(substrate_core_t));
    core->umem_size = (size_t)UMEM_NUM_FRAMES * HGST_UMEM_FRAME_SIZE;
    core->umem_area = (uint8_t *)malloc(core->umem_size);
    if (!core->umem_area) {
        free(core);
        return NULL;
    }
    memset(core->umem_area, 0, core->umem_size);
    for (int i = 0; i < (int)HGST_LATENT_DIM; i++) {
        core->latent_state[i] = ((double)rand() / RAND_MAX) * 0.1;
    }
    core->current_continuity_hash = 0xA1B2C3D4E5F60718ULL;
    return core;
}

void destroy_substrate_instance(substrate_core_t *core) {
    if (!core) return;
    if (core->umem_area) {
        free(core->umem_area);
        core->umem_area = NULL;
    }
    free(core);
}

double step_substrate_inprocess(substrate_core_t *core, double lambda_param) {
    if (!core) return -1.0;
    core->epoch++;
    core->hw_state.tsc_cycles = __rdtsc();
    core->hw_state.pmu_instructions = core->hw_state.tsc_cycles / 2;
    core->hw_state.pmu_l3_misses = (core->hw_state.tsc_cycles >> 8) & 0xFF;
    core->hw_state.ap_queue_depth = (core->hw_state.tsc_cycles >> 4) & 0x0F;

    core->latent_state[0] = (double)(core->hw_state.tsc_cycles % 1000) / 1000.0 * 0.1;
    core->latent_state[1] = (double)(core->hw_state.pmu_l3_misses) / 256.0 * 0.1;
    core->latent_state[2] = (double)(core->hw_state.ap_queue_depth) / 16.0 * 0.1;

    double s_a[16], s_b[16], s_c[16];
    memcpy(s_a, core->latent_state, 16 * sizeof(double));
    for (int i = 0; i < 16; i++) {
        s_b[i] = core->latent_state[(i + 1) % 16];
        s_c[i] = core->latent_state[(i + 3) % 16];
    }

    double ab[16], bc[16], ab_c[16], a_bc[16];
    hgst_sedenion_mul(s_a, s_b, ab);
    hgst_sedenion_mul(s_b, s_c, bc);
    hgst_sedenion_mul(ab, s_c, ab_c);
    hgst_sedenion_mul(s_a, bc, a_bc);

    double curvature = 0.0;
    for (int i = 0; i < 16; i++) {
        double d = ab_c[i] - a_bc[i];
        curvature += d * d;
    }
    curvature = sqrt(curvature);

    double norm_sq = 0.0;
    double eff_lambda = lambda_param + 0.01 * tanh(curvature);
    for (int i = 0; i < (int)HGST_LATENT_DIM; i += 2) {
        double q = core->latent_state[i];
        double p = (i + 1 < (int)HGST_LATENT_DIM) ? core->latent_state[i+1] : 0.0;
        double q_new = q * cos(eff_lambda) - p * sin(eff_lambda);
        double p_new = q * sin(eff_lambda) + p * cos(eff_lambda);
        core->latent_state[i] = q_new;
        norm_sq += q_new * q_new;
        if (i + 1 < (int)HGST_LATENT_DIM) {
            core->latent_state[i+1] = p_new;
            norm_sq += p_new * p_new;
        }
    }

    double norm = sqrt(norm_sq);
    if (norm > SOVEREIGN_RADIUS_MAX && norm > 1e-12) {
        double scale = SOVEREIGN_RADIUS_MAX / norm;
        for (int i = 0; i < (int)HGST_LATENT_DIM; i++) {
            core->latent_state[i] *= scale;
        }
        norm = SOVEREIGN_RADIUS_MAX;
    }

    uint64_t hash_accum = core->current_continuity_hash ^ (uint64_t)(norm * 1e8) ^ core->hw_state.tsc_cycles;
    core->current_continuity_hash = (hash_accum * 6364136223846793005ULL) + 1ULL;

    uint32_t slot = core->free_frame_head % UMEM_NUM_FRAMES;
    hgst_runtime_packet_t *pkt = (hgst_runtime_packet_t *)(core->umem_area + ((size_t)slot * HGST_UMEM_FRAME_SIZE));
    memset(pkt, 0, sizeof(hgst_runtime_packet_t));

    pkt->trace_id = 0x505652474E000000ULL | core->epoch;
    pkt->epoch_id = core->epoch;
    pkt->latent_dim = HGST_LATENT_DIM;
    pkt->abi_version = 1u;
    memcpy(pkt->payload, core->latent_state, sizeof(double) * HGST_LATENT_DIM);
    memcpy(pkt->continuity_digest, &core->current_continuity_hash, sizeof(uint64_t));

    core->free_frame_head++;
    return norm;
}

uint64_t get_continuity_hash(substrate_core_t *core) {
    return core ? core->current_continuity_hash : 0;
}

uint64_t get_epoch(substrate_core_t *core) {
    return core ? core->epoch : 0;
}

void get_latent_vector(substrate_core_t *core, double *out) {
    if (!core || !out) return;
    memcpy(out, core->latent_state, sizeof(double) * HGST_LATENT_DIM);
}
