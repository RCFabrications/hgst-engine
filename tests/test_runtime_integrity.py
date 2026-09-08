import unittest
from hgst.runtime_integrity import EventLedger, ExecutionClosure, RunManifest

class TestRuntimeIntegrity(unittest.TestCase):
    def test_hash_chain_detects_mutation(self):
        ledger = EventLedger()
        ledger.append("run.started", {"seed": 42})
        ledger.append("run.completed", {"result_hash": "a" * 64})
        self.assertTrue(ledger.verify())
        ledger.events[-1] = ledger.events[-1].__class__(2, "run.completed", {"result_hash": "b" * 64}, ledger.events[-1].parent_hash, ledger.events[-1].event_hash)
        self.assertFalse(ledger.verify())

    def test_closure_binds_revision_and_inputs(self):
        manifest = RunManifest("abc", "3.10", 42, {"lambda": 0.05})
        base = ExecutionClosure({"module": "hgst.engine"}, {"x": [1, 2]}, "abc", ("d" * 64,), manifest.run_id)
        changed = ExecutionClosure({"module": "hgst.engine"}, {"x": [1, 3]}, "abc", ("d" * 64,), manifest.run_id)
        self.assertNotEqual(base.closure_hash, changed.closure_hash)

if __name__ == "__main__":
    unittest.main()
