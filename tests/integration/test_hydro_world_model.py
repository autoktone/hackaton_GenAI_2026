"""Hydro application projection through the actual unmodified World Model reference."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from agent.hydro import HydroAnalyzer, HydroStubProvider, SnapshotSqlExecutor, HYDRO_QUESTION
from agent.hydro_catalog import CATALOG_VERSION, catalog_digest
from agent.execution_state import ExecutionStateStore
from agent.orchestrator import Orchestrator
from agent.world_model import SubprocessTransport, WorldModelClient


class HydroWorldModelTests(unittest.TestCase):
    def setUp(self):
        snapshot_path = Path(__file__).resolve().parents[2] / "data/snapshots/hubeau-givry-2026-10-27.json"
        self.snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.client = WorldModelClient(SubprocessTransport(profile="memory", timeout=10))
        self.addCleanup(self.client.close)
        self.store = ExecutionStateStore(self.client)
        self.enterContext(patch("socket.create_connection", side_effect=AssertionError("No platform network.")))

    def run_hydro(self, **kwargs):
        return Orchestrator(HydroAnalyzer(HydroStubProvider()),
            SnapshotSqlExecutor(self.snapshot), execution_store=self.store).run(
                HYDRO_QUESTION, context={"catalogVersion": CATALOG_VERSION,
                                        "catalogDigest": catalog_digest()}, **kwargs)

    def test_actual_engine_has_two_data_tasks_and_catalog_identity(self):
        result = self.run_hydro()
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        state = result["worldModel"]
        run = state["state"]["run"]
        self.assertEqual(run["status"], "SUCCEEDED")
        self.assertEqual(run["profile"]["sourceKind"], "captured_real_snapshot")
        self.assertEqual(run["context"]["catalogVersion"], CATALOG_VERSION)
        self.assertEqual(len(run["tasks"]), 5)
        self.assertTrue(all(t["status"] == "COMPLETED" for t in run["tasks"].values()))
        self.assertEqual(state["nativeEventCount"], len(result["trace"]) + 1)
        self.assertEqual(state["nativeAuditCount"], state["nativeEventCount"])
        self.assertLessEqual(state["nativeEventCount"], 32)
        self.assertFalse(result["durableTrace"])
        self.assertFalse(result["workflowExecuted"])

    def test_same_user_overlapping_hydro_runs_keep_histories_and_receipts_separate(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.run_hydro, run_id="HYDRO-" + suffix,
                                   request_id="REQ-" + suffix) for suffix in ["A", "B"]]
            first, second = [f.result(timeout=60) for f in futures]
        for result in [first, second]:
            self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertNotEqual(first["worldModel"]["namespace"], second["worldModel"]["namespace"])
        histories = [{e["eventId"] for e in r["worldModel"]["state"]["run"]["history"]}
                     for r in [first, second]]
        self.assertTrue(histories[0].isdisjoint(histories[1]))
        receipts = [{r["evidenceId"] for r in result["analysisResult"]["datasets"]}
                    for result in [first, second]]
        self.assertTrue(receipts[0].isdisjoint(receipts[1]))


if __name__ == "__main__":
    unittest.main()
