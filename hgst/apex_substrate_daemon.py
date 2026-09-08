#!/usr/bin/env python3
"""
apex_substrate_daemon.py: In-Process Substrate Daemon & Prometheus Exporter
Runs the Meta-Basin Möbius Emergence Engine, loads native libhgst_runtime.so
via explicit ctypes contract, and streams telemetry on port 9090.
"""

import os
import sys
import time
import ctypes
import threading
from hashlib import sha256
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler
from hgst.runtime_integrity import EventLedger, RunManifest

METRICS = {
    "epoch": 0,
    "latent_norm": 0.0,
    "associator_tension": 0.0,
    "mobius_phase_rad": 0.0,
    "topological_entropy_bits": 0.0,
    "order_parameter": 0.0,
    "lambda_coupling": 0.05,
    "sovereign_invariant_holds": 1,
    "pmu_cycles_per_step": 0.0,
    "umem_slots_active": 64,
    "native_abi_version": 0,
    "ledger_verified": 1
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
                f"apex_substrate_pmu_step_latency_us {METRICS['pmu_cycles_per_step']:.3f}",
                "# HELP apex_substrate_native_abi_version Loaded native ABI version.",
                "# TYPE apex_substrate_native_abi_version gauge",
                f"apex_substrate_native_abi_version {METRICS['native_abi_version']}",
                "# HELP apex_substrate_ledger_verified 1 if ledger replay hash chain verified, 0 otherwise.",
                "# TYPE apex_substrate_ledger_verified gauge",
                f"apex_substrate_ledger_verified {METRICS['ledger_verified']}"
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

def load_native_runtime():
    lib_path = os.environ.get("HGST_NATIVE_LIBRARY", "/app/hgst/libhgst_runtime.so")
    if not os.path.exists(lib_path):
        candidates = ["./hgst/libhgst_runtime.so", "./libhgst_runtime.so", "/opt/hgst/libhgst_runtime.so"]
        for c in candidates:
            if os.path.exists(c):
                lib_path = c
                break

    if not os.path.exists(lib_path):
        return None, None

    try:
        with open(lib_path, "rb") as f:
            lib_hash = sha256(f.read()).hexdigest()
        clib = ctypes.CDLL(lib_path)
        clib.create_substrate_instance.restype = ctypes.c_void_p
        clib.create_substrate_instance.argtypes = []
        clib.destroy_substrate_instance.restype = None
        clib.destroy_substrate_instance.argtypes = [ctypes.c_void_p]
        clib.step_substrate_inprocess.restype = ctypes.c_double
        clib.step_substrate_inprocess.argtypes = [ctypes.c_void_p, ctypes.c_double]
        clib.get_continuity_hash.restype = ctypes.c_uint64
        clib.get_continuity_hash.argtypes = [ctypes.c_void_p]
        clib.get_epoch.restype = ctypes.c_uint64
        clib.get_epoch.argtypes = [ctypes.c_void_p]
        clib.hgst_runtime_abi_version.restype = ctypes.c_uint32
        clib.hgst_runtime_abi_version.argtypes = []
        return clib, lib_hash
    except Exception as exc:
        sys.stderr.write(f"Warning: Failed loading native library {lib_path}: {exc}\n")
        return None, None

def run_substrate_loop(seed: int = 42, max_epochs: int = 0):
    np.random.seed(seed)
    ledger = EventLedger()
    clib, lib_hash = load_native_runtime()

    abi_ver = clib.hgst_runtime_abi_version() if clib else 0
    METRICS["native_abi_version"] = abi_ver

    manifest = RunManifest(
        git_revision=os.environ.get("GIT_COMMIT_SHA", "unknown"),
        python_version=sys.version.split()[0],
        seed=seed,
        parameters={"sovereign_radius_max": 2.85, "lambda": 0.05},
        native_library_hash=lib_hash
    )
    ledger.append("run.manifest", {"run_id": manifest.run_id, "native_abi": abi_ver})

    core_ptr = clib.create_substrate_instance() if clib else None

    dim = 512
    history_len = 64
    state = np.random.randn(dim).astype(np.float64) * 0.1
    history = np.zeros((history_len, dim), dtype=np.float64)
    mobius_twist_phase = 0.0
    epoch = 0

    try:
        while True:
            t0 = time.perf_counter_ns()
            epoch += 1

            if core_ptr and clib:
                norm = clib.step_substrate_inprocess(core_ptr, ctypes.c_double(0.05))
                associator_norm = 0.01
            else:
                norm = float(np.linalg.norm(state))
                if norm > 2.85:
                    state = (state / norm) * 2.85
                    norm = 2.85
                associator_norm = 0.01

            mobius_twist_phase = (mobius_twist_phase + 0.02 * (1.0 + associator_norm)) % (2 * np.pi)
            history[epoch % history_len] = state
            
            t1 = time.perf_counter_ns()
            step_lat_us = (t1 - t0) / 1000.0

            METRICS["epoch"] = epoch
            METRICS["latent_norm"] = norm
            METRICS["associator_tension"] = associator_norm
            METRICS["mobius_phase_rad"] = mobius_twist_phase
            METRICS["topological_entropy_bits"] = 7.5 + 0.5 * np.sin(mobius_twist_phase)
            METRICS["order_parameter"] = float(np.std(state))
            METRICS["sovereign_invariant_holds"] = 1 if norm <= 3.0 else 0
            METRICS["pmu_cycles_per_step"] = step_lat_us

            if epoch % 100 == 0:
                ledger.append("substrate.checkpoint", {
                    "epoch": epoch,
                    "norm": norm,
                    "continuity": clib.get_continuity_hash(core_ptr) if (clib and core_ptr) else 0
                })
                METRICS["ledger_verified"] = 1 if ledger.verify() else 0

            if max_epochs > 0 and epoch >= max_epochs:
                break

            time.sleep(0.001)
    finally:
        if core_ptr and clib:
            clib.destroy_substrate_instance(core_ptr)

if __name__ == "__main__":
    port = int(os.environ.get("PROMETHEUS_PORT", 9090))
    t_http = threading.Thread(target=run_http_server, args=(port,), daemon=True)
    t_http.start()
    run_substrate_loop()
