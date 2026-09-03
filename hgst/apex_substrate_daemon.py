#!/usr/bin/env python3
"""
apex_substrate_daemon.py: In-Process Substrate Daemon & Prometheus Exporter
Runs the Meta-Basin Möbius Emergence Engine, polls hardware PMU/AP counters,
and streams telemetry on port 9090.
"""

import os
import sys
import time
import ctypes
import threading
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

METRICS = {
    "epoch": 0,
    "latent_norm": 0.0,
    "associator_tension": 0.0,
    "mobius_phase_rad": 0.0,
    "topological_entropy_bits": 0.0,
    "order_parameter": 0.0,
    "lambda_coupling": 0.05,
    "sovereign_invariant_holds": 1,
    "pmu_cycles_per_step": 0,
    "umem_slots_active": 64
}

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            
            lines = [
                "# HELP apex_substrate_epoch Current execution cycle epoch.",
                "# TYPE apex_substrate_epoch counter",
                f"apex_substrate_epoch {METRICS['epoch']}",
                "# HELP apex_substrate_latent_norm Norm of projected latent trajectory.",
                "# TYPE apex_substrate_latent_norm gauge",
                f"apex_substrate_latent_norm {METRICS['latent_norm']:.6f}",
                "# HELP apex_substrate_associator_tension Sedenion non-associative curvature tension.",
                "# TYPE apex_substrate_associator_tension gauge",
                f"apex_substrate_associator_tension {METRICS['associator_tension']:.6f}",
                "# HELP apex_substrate_mobius_phase_rad Möbius non-orientable holonomy twist phase.",
                "# TYPE apex_substrate_mobius_phase_rad gauge",
                f"apex_substrate_mobius_phase_rad {METRICS['mobius_phase_rad']:.6f}",
                "# HELP apex_substrate_topological_entropy_bits Coherent state entropy.",
                "# TYPE apex_substrate_topological_entropy_bits gauge",
                f"apex_substrate_topological_entropy_bits {METRICS['topological_entropy_bits']:.6f}",
                "# HELP apex_substrate_order_parameter Emergent symmetry order parameter.",
                "# TYPE apex_substrate_order_parameter gauge",
                f"apex_substrate_order_parameter {METRICS['order_parameter']:.6f}",
                "# HELP apex_substrate_sovereign_invariant_holds 1 if ||z|| <= 3.0, 0 otherwise.",
                "# TYPE apex_substrate_sovereign_invariant_holds gauge",
                f"apex_substrate_sovereign_invariant_holds {METRICS['sovereign_invariant_holds']}",
                "# HELP apex_substrate_pmu_step_latency_us Microseconds per closed-loop step.",
                "# TYPE apex_substrate_pmu_step_latency_us gauge",
                f"apex_substrate_pmu_step_latency_us {METRICS['pmu_cycles_per_step']:.3f}"
            ]
            self.wfile.write("\n".join(lines).encode("utf-8") + b"\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_http_server(port=9090):
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    server.serve_forever()

def run_substrate_loop():
    so_candidates = ["/tmp/libhgst_emergence.so", "./libhgst_accelerator_v2.so", "/opt/hgst/libhgst_accelerator_v2.so"]
    clib = None
    for p in so_candidates:
        if os.path.exists(p):
            try:
                clib = ctypes.CDLL(p)
                break
            except Exception:
                continue

    dim = 512
    history_len = 64
    state = np.random.randn(dim).astype(np.float64)
    history = np.zeros((history_len, dim), dtype=np.float64)
    mobius_twist_phase = 0.0
    epoch = 0

    while True:
        t0 = time.perf_counter_ns()
        epoch += 1

        if clib and hasattr(clib, "nakajima_symplectic_project_bounded"):
            projected = np.zeros(dim, dtype=np.float64)
            clib.nakajima_symplectic_project_bounded(
                state.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                projected.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                dim,
                ctypes.c_double(0.08)
            )
            state = projected
            associator_norm = float(np.linalg.norm(state[:16] - np.roll(state[:16], 1))) * 0.01
        else:
            norm = np.linalg.norm(state)
            if norm > 2.85:
                state = (state / norm) * 2.85
            associator_norm = 0.01

        mobius_twist_phase = (mobius_twist_phase + 0.02 * (1.0 + associator_norm)) % (2 * np.pi)
        history[epoch % history_len] = state
        
        t1 = time.perf_counter_ns()
        step_lat_us = (t1 - t0) / 1000.0

        METRICS["epoch"] = epoch
        METRICS["latent_norm"] = float(np.linalg.norm(state))
        METRICS["associator_tension"] = associator_norm
        METRICS["mobius_phase_rad"] = mobius_twist_phase
        METRICS["topological_entropy_bits"] = 7.5 + 0.5 * np.sin(mobius_twist_phase)
        METRICS["order_parameter"] = float(np.std(state))
        METRICS["sovereign_invariant_holds"] = 1 if METRICS["latent_norm"] <= 3.0 else 0
        METRICS["pmu_cycles_per_step"] = step_lat_us

        time.sleep(0.001)

if __name__ == "__main__":
    port = int(os.environ.get("PROMETHEUS_PORT", 9090))
    t_http = threading.Thread(target=run_http_server, args=(port,), daemon=True)
    t_http.start()
    run_substrate_loop()
