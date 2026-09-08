#ifndef HGST_RUNTIME_ABI_H
#define HGST_RUNTIME_ABI_H

#include <stdint.h>
#include <stddef.h>

#define HGST_LATENT_DIM 512u
#define HGST_PACKET_HEADER_BYTES 24u
#define HGST_PACKET_SIGNATURE_BYTES 32u
#define HGST_PACKET_BYTES (HGST_PACKET_HEADER_BYTES + (HGST_LATENT_DIM * sizeof(double)) + HGST_PACKET_SIGNATURE_BYTES)
#define HGST_UMEM_FRAME_SIZE 8192u

typedef struct {
    uint64_t trace_id;
    uint64_t epoch_id;
    uint32_t latent_dim;
    uint32_t abi_version;
    double payload[HGST_LATENT_DIM];
    uint8_t continuity_digest[HGST_PACKET_SIGNATURE_BYTES];
} hgst_runtime_packet_t;

_Static_assert(sizeof(hgst_runtime_packet_t) <= HGST_UMEM_FRAME_SIZE, "HGST packet exceeds UMEM frame");

#endif
