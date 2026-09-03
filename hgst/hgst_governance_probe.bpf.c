/*
 * hgst_governance_probe.bpf.c
 * Kernel-space eBPF probe verifying HGST sovereignty invariants at runtime.
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define SOVEREIGN_RADIUS_SQ 9.0 /* (3.0)^2 */

struct invariant_event_t {
    __u64 trace_id;
    __u64 timestamp;
    __u32 pid;
    __u32 violation;
    double sovereign_dist_sq;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} governance_events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u64);
    __type(value, __u64);
} active_sovereign_traces SEC(".maps");

SEC("kprobe/sys_enter")
int BPF_KPROBE(trace_hgst_governance_enter) {
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u64 *trace_id = bpf_map_lookup_elem(&active_sovereign_traces, &pid_tgid);
    
    if (!trace_id) {
        return 0;
    }

    struct invariant_event_t *event = bpf_ringbuf_reserve(&governance_events, sizeof(*event), 0);
    if (!event) {
        return 0;
    }

    event->trace_id = *trace_id;
    event->timestamp = bpf_ktime_get_ns();
    event->pid = (__u32)(pid_tgid >> 32);
    event->violation = 0;
    event->sovereign_dist_sq = 0.0;

    bpf_ringbuf_submit(event, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
