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

#define LATENT_DIM 512
#define UMEM_NUM_FRAMES 256
#define UMEM_FRAME_SIZE 4096
#define SOVEREIGN_RADIUS_MAX 2.85

typedef struct {
    uint64_t tsc_cycles;
    uint64_t pmu_instructions;
    uint64_t pmu_l3_misses;
    uint64_t ap_queue_depth;
} hardware_telemetry_t;

typedef struct {
    uint8_t  eth_hdr[14];
    uint8_t  ip_hdr[20];
    uint8_t  udp_hdr[8];
    uint64_t trace_id;
    uint64_t epoch_id;
    uint32_t latent_dim;
    uint32_t reserved;
    double   payload[LATENT_DIM];
    uint8_t  pow_signature[32];
} xsk_wire_packet_t;

typedef struct {
    uint8_t               *umem_area;
    size_t                umem_size;
    uint32_t              free_frame_head;
    uint64_t              epoch;
    uint64_t              current_continuity_hash;
    double                latent_state[LATENT_DIM];
    hardware_telemetry_t  hw_state;
} substrate_core_t;

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

static inline void sedenion_mul(const double *a, const double *b, double *out) {
    memset(out, 0, sizeof(double) * 16);
    for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
            uint8_t k = CD_INDEX[i][j];
            int8_t s = CD_SIGNS[i][j];
            out[k] += s * a[i] * b[j];
        }
    }
}

substrate_core_t* create_substrate_instance() {
    substrate_core_t *core = (substrate_core_t *)malloc(sizeof(substrate_core_t));
    memset(core, 0, sizeof(substrate_core_t));
    core->umem_size = UMEM_NUM_FRAMES * UMEM_FRAME_SIZE;
    core->umem_area = (uint8_t *)malloc(core->umem_size);
    memset(core->umem_area, 0, core->umem_size);
    for (int i = 0; i < LATENT_DIM; i++) {
        core->latent_state[i] = ((double)rand() / RAND_MAX) * 0.1;
    }
    core->current_continuity_hash = 0xA1B2C3D4E5F60718ULL;
    return core;
}

double step_substrate_inprocess(substrate_core_t *core, double lambda_param) {
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
    sedenion_mul(s_a, s_b, ab);
    sedenion_mul(s_b, s_c, bc);
    sedenion_mul(ab, s_c, ab_c);
    sedenion_mul(s_a, bc, a_bc);

    double curvature = 0.0;
    for (int i = 0; i < 16; i++) {
        double d = ab_c[i] - a_bc[i];
        curvature += d * d;
    }
    curvature = sqrt(curvature);

    double norm_sq = 0.0;
    double eff_lambda = lambda_param + 0.01 * tanh(curvature);
    for (int i = 0; i < LATENT_DIM; i += 2) {
        double q = core->latent_state[i];
        double p = (i + 1 < LATENT_DIM) ? core->latent_state[i+1] : 0.0;
        double q_new = q * cos(eff_lambda) - p * sin(eff_lambda);
        double p_new = q * sin(eff_lambda) + p * cos(eff_lambda);
        core->latent_state[i] = q_new;
        norm_sq += q_new * q_new;
        if (i + 1 < LATENT_DIM) {
            core->latent_state[i+1] = p_new;
            norm_sq += p_new * p_new;
        }
    }

    double norm = sqrt(norm_sq);
    if (norm > SOVEREIGN_RADIUS_MAX && norm > 1e-12) {
        double scale = SOVEREIGN_RADIUS_MAX / norm;
        for (int i = 0; i < LATENT_DIM; i++) {
            core->latent_state[i] *= scale;
        }
        norm = SOVEREIGN_RADIUS_MAX;
    }

    uint64_t hash_accum = core->current_continuity_hash ^ (uint64_t)(norm * 1e8) ^ core->hw_state.tsc_cycles;
    core->current_continuity_hash = (hash_accum * 6364136223846793005ULL) + 1ULL;

    uint32_t slot = core->free_frame_head % UMEM_NUM_FRAMES;
    xsk_wire_packet_t *pkt = (xsk_wire_packet_t *)(core->umem_area + (slot * UMEM_FRAME_SIZE));

    memset(pkt->eth_hdr, 0x02, 6);
    memset(pkt->eth_hdr + 6, 0x06, 6);
    pkt->eth_hdr[12] = 0x08;
    pkt->eth_hdr[13] = 0x00;

    pkt->trace_id = 0x505652474E000000ULL | core->epoch;
    pkt->epoch_id = core->epoch;
    pkt->latent_dim = LATENT_DIM;
    memcpy(pkt->payload, core->latent_state, sizeof(double) * LATENT_DIM);
    memcpy(pkt->pow_signature, &core->current_continuity_hash, sizeof(uint64_t));

    core->free_frame_head++;
    return norm;
}

uint64_t get_continuity_hash(substrate_core_t *core) {
    return core->current_continuity_hash;
}

uint64_t get_epoch(substrate_core_t *core) {
    return core->epoch;
}

void get_latent_vector(substrate_core_t *core, double *out) {
    memcpy(out, core->latent_state, sizeof(double) * LATENT_DIM);
}
