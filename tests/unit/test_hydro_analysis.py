"""Standalone hydro contracts: captured data, strict SQL and bounded catalog-aware loops."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import Mock, patch

from agent.hydro import (
    HydroAnalyzer, HydroSqlExecutor, HydroStubProvider, SnapshotSqlExecutor,
    STATION_SQL, OBSERVATIONS_SQL, HYDRO_QUESTION, summarize_result,
)
from agent.hydro_catalog import CATALOG, HydroQueryPolicy, SCHEMAS, catalog_digest
from agent.llm import ProviderError
from agent.main import main
from agent.orchestrator import Orchestrator
from agent.tools_zetaris import SqlError, ZetarisHttpTransport, ZetarisSettings

SNAPSHOT = Path(__file__).resolve().parents[2] / "data/snapshots/hubeau-givry-2026-10-27.json"
OPERATION = "00000000-0000-4000-8000-000000000002"


class ScriptedProvider:
    kind = "standalone_stub"
    route = "standalone_stub"

    def __init__(self, queries):
        self.queries = queries
        self.requests = []

    def complete(self, messages, **kwargs):
        self.requests.append(copy.deepcopy(messages))
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if len(results) < len(self.queries):
            index = len(results)
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_" + str(index), "type": "function", "function": {
                    "name": "run_sql", "arguments": json.dumps({"sql": self.queries[index]})}}]}
        else:
            message = {"role": "assistant", "content":
                       "Observed evidence, not a forecast: "
                       + ", ".join(r["evidenceId"] for r in results)}
        return {"model": "standalone_stub", "choices": [{"message": message}]}


class HydroStandaloneTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.policy = HydroQueryPolicy()
        self.executor = SnapshotSqlExecutor(self.snapshot)
        self.enterContext(patch("socket.create_connection", side_effect=AssertionError("No network.")))
        self.enterContext(patch("subprocess.run", side_effect=AssertionError("No native process.")))
        self.enterContext(patch("pathlib.Path.read_text", side_effect=AssertionError("No private files.")))

    def execute(self, sql=OBSERVATIONS_SQL):
        return self.executor.execute(sql, operation_id=OPERATION)

    def run_analysis(self, provider=None, executor=None, **kwargs):
        return Orchestrator(HydroAnalyzer(provider or HydroStubProvider()),
                            executor or self.executor).run(HYDRO_QUESTION, **kwargs)

    def test_all_authorized_sources_are_available(self):
        for view, schema in SCHEMAS.items():
            with self.subTest(view=view):
                result = self.execute("SELECT * FROM " + view + " LIMIT 50")
                self.assertEqual(result["columns"], [col for col, _ in schema])
                self.assertGreater(result["rowCount"], 0)

    def test_catalog_exposes_units_coverage_quality_and_unavailable_weather(self):
        encoded = json.dumps(CATALOG)
        for value in ["m3/s", "1000", "code_site", "No matching", "Meteo-France", "H-MEM"]:
            self.assertIn(value, encoded)
        self.assertEqual(len(catalog_digest()), 64)

    def test_missing_limit_is_capped_and_proposed_vs_executed_sql_are_traced(self):
        proposed = STATION_SQL.rsplit(" LIMIT ", 1)[0]
        self.assertEqual(self.policy.prepare(proposed), proposed + " LIMIT 50")
        result = self.run_analysis(ScriptedProvider([proposed]))
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        requested = next(e for e in result["trace"] if e["eventType"] == "TOOL_REQUEST_RECEIVED")
        dispatched = next(e for e in result["trace"] if e["eventType"] == "SQL_DISPATCHED")
        self.assertEqual(requested["payload"]["sql"], proposed)
        self.assertEqual(dispatched["payload"]["sql"], proposed + " LIMIT 50")
        self.assertEqual(result["analysisResult"]["data"]["rowCount"], 1)

    def test_actual_multiline_or_proposal_is_admitted_with_bounded_result(self):
        proposed = "SELECT code_station, code_site, libelle_station, libelle_site, libelle_commune, libelle_departement, libelle_cours_eau, en_service, latitude_station, longitude_station, date_ouverture_station, date_fermeture_station\nFROM flood_analysis.v_hydro_stations\nWHERE code_station = 'K400001010' OR code_site = 'K400001010'\nLIMIT 1"
        result = self.run_analysis(ScriptedProvider([proposed]))
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["analysisResult"]["data"]["rowCount"], 1)
        dispatched = next(e for e in result["trace"] if e["eventType"] == "SQL_DISPATCHED")
        self.assertNotIn("\n", dispatched["payload"]["sql"])
        self.assertTrue(dispatched["payload"]["sql"].endswith("LIMIT 1"))

    def test_station_and_site_context_and_text_search_are_consistent(self):
        context = CATALOG["knownStationContexts"][0]
        self.assertEqual(context["code_station"], "K400001010")
        self.assertEqual(context["code_site"], "K4000010")
        sql = ("SELECT * FROM flood_analysis.v_hydro_stations "
               "WHERE libelle_commune LIKE '%Givry%' OR libelle_station LIKE '%Givry%'")
        result = self.execute(sql)
        self.assertEqual(result["rowCount"], 1)
        self.assertEqual(result["rows"][0][0], context["code_station"])

    def test_layout_normalization_does_not_change_quoted_values(self):
        sql = ("SELECT code_station FROM flood_analysis.v_hydro_stations\n"
               "WHERE libelle_station='two  spaces OR text' LIMIT 1")
        prepared = self.policy.prepare(sql)
        self.assertIn("'two  spaces OR text'", prepared)
        self.assertEqual(self.execute(sql)["rows"], [])

    def test_rejected_sql_proposal_remains_visible_without_dispatch(self):
        proposed = "SELECT * FROM private.secret LIMIT 1"
        result = self.run_analysis(ScriptedProvider([proposed]))
        self.assertEqual(result["counts"]["toolExecutions"], 0)
        request = next(e for e in result["trace"] if e["eventType"] == "TOOL_REQUEST_RECEIVED")
        self.assertEqual(request["payload"]["sql"], proposed)
        self.assertFalse(any(e["eventType"] == "SQL_DISPATCHED" for e in result["trace"]))

    def test_weather_catalog_reads_raw_rows_without_python_weather_analysis(self):
        sql = ("SELECT * FROM flood_hydro.meteo_precipitations_raw "
               "WHERE NUM_POSTE = 44015001 ORDER BY AAAAMMJJ ASC LIMIT 5")
        result = self.execute(sql)
        self.assertEqual(result["columns"],
                         ["NUM_POSTE", "NOM_USUEL", "LAT", "LON", "AAAAMMJJ", "RR", "QRR"])
        self.assertEqual(result["rows"][0],
                         [44015001, "BLAIN", 47.472833, -1.771667, 20240101, 37.6, 1])
        self.assertEqual(summarize_result(result)["series"], [])
        self.assertEqual(CATALOG["precipitationCoverage"]["verifiedRows"], 5490)
        self.assertEqual(CATALOG["precipitationCoverage"]["firstDay"], 20240101)

    def test_projection_filters_order_and_pagination(self):
        sql = ("SELECT date_obs, valeur_normalisee FROM flood_analysis.v_hydro_observations "
               "WHERE code_station = 'K400001010' AND grandeur_hydro = 'Q' "
               "ORDER BY date_obs ASC LIMIT 2 OFFSET 1")
        result = self.execute(sql)
        self.assertEqual(result["rows"],
                         [["2026-10-27T17:55:00Z", 50.6], ["2026-10-27T18:00:00Z", 50.6]])
        self.assertTrue(result["truncated"])

    def test_aggregates_describe_only_captured_rows(self):
        query = ("SELECT COUNT(*) AS n, MIN(valeur_normalisee) AS lo, "
                 "MAX(valeur_normalisee) AS hi, AVG(valeur_normalisee) AS mean "
                 "FROM flood_analysis.v_hydro_observations WHERE grandeur_hydro = 'Q' LIMIT 1")
        row = self.execute(query)["rows"][0]
        self.assertEqual(row[:3], [3, 50.6, 50.6])
        self.assertAlmostEqual(row[3], 50.6)

    def test_injections_unsupported_grammar_and_unknown_sources_fail_closed(self):
        bad = [
            "DELETE FROM flood_analysis.v_hydro_observations",
            STATION_SQL + "; SELECT 1",
            STATION_SQL + " -- comment",
            "SELECT * FROM flood_analysis.v_hydro_stations LIMIT 1 UNION SELECT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'x' OR 1=1 LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'x' AND LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'x';-- LIMIT 1",
            "SELECT secret FROM flood_analysis.v_hydro_stations LIMIT 1",
            "SELECT * FROM POKEAPI_REST.pokemon LIMIT 1",
            "SELECT * FROM flood_analysis.v_meteo_precipitations LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations JOIN other LIMIT 1",
            "SELECT sleep(30) FROM flood_analysis.v_hydro_stations LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations LIMIT 51",
            "SELECT * FROM flood_analysis.v_hydro_stations LIMIT 0",
            "SELECT * FROM flood_analysis.v_hydro_stations LIMIT 1 OFFSET 100001",
            "SELECT code_station, COUNT(*) FROM flood_analysis.v_hydro_stations LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations ORDER BY secret LIMIT 1",
            "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'x' /*x*/ LIMIT 1",
        ]
        for sql in bad:
            with self.subTest(sql=sql), self.assertRaises(SqlError):
                self.execute(sql)

    def test_real_values_and_missing_metadata_are_preserved(self):
        result = self.execute()
        self.assertEqual(result["rows"][0][5], -1.46)
        self.assertEqual(result["rows"][1][5], 50.6)
        station = self.execute(STATION_SQL)
        self.assertIs(station["rows"][0][7], True)
        self.assertIsNone(station["rows"][0][11])
        self.assertEqual(station["sourceKind"], "captured_real_snapshot")

    def test_live_and_snapshot_share_the_same_tool_result_shape_and_values(self):
        transport = Mock(timeout_seconds=15)
        transport.post_query.return_value = {
            "data": self.snapshot["views"]["flood_analysis.v_hydro_observations"]["rows"]}
        live = HydroSqlExecutor(transport).execute(OBSERVATIONS_SQL, operation_id=OPERATION)
        snapshot = self.execute()
        self.assertEqual(set(live), set(snapshot))
        for key in ["columns", "rows", "rowCount", "truncated", "operationId"]:
            self.assertEqual(live[key], snapshot[key])
        self.assertEqual(live["sourceKind"], "zetaris_rest")

    def test_disallowed_query_is_rejected_before_live_transport(self):
        transport = Mock(timeout_seconds=15)
        with self.assertRaises(SqlError):
            HydroSqlExecutor(transport).execute("DROP TABLE x", operation_id=OPERATION)
        transport.post_query.assert_not_called()

    def test_malformed_nonfinite_and_wrong_width_responses_are_rejected(self):
        for rows in [None, {}, [[1, 2]], [["nan"]], [[True]]]:
            with self.subTest(rows=rows), self.assertRaises(SqlError):
                self.policy.result("SELECT valeur_normalisee FROM flood_analysis.v_hydro_observations LIMIT 1",
                                   rows, operation_id=OPERATION, source_kind="zetaris_rest")

    def test_receipts_are_scoped_and_types_are_strict(self):
        for mutation in [
            lambda r: r.update(operationId=str(uuid.uuid4())),
            lambda r: r.update(rowCount=True),
            lambda r: r.update(sourceKind="zetaris_rest"),
            lambda r: r.update(truncated="false"),
            lambda r: r["rows"][0].__setitem__(5, "-1.46"),
        ]:
            result = self.execute()
            mutation(result)
            with self.assertRaises(SqlError):
                self.executor.validate_result(result, sql=OBSERVATIONS_SQL, operation_id=OPERATION)

    def test_deterministic_summary_has_three_points_per_variable_and_no_forecast(self):
        summary = summarize_result(self.execute())
        self.assertEqual(len(summary["series"]), 2)
        for series in summary["series"]:
            self.assertEqual(series["distinctTimes"], 3)
            self.assertEqual(series["windowMinutes"], 10)
            self.assertEqual(series["firstToLastChange"], 0)
            self.assertIn("Non qualifi\u00e9e", series["qualityLabels"])
        self.assertIn("No rainfall/discharge lag", " ".join(summary["warnings"]))

    def test_invalid_units_and_missing_values_are_excluded_not_replaced(self):
        result = self.execute()
        result["rows"][0][6] = "cm"
        result["rows"][1][5] = None
        result["rows"][2][2] = "2026-10-27T17:55:00"
        summary = summarize_result(result)
        self.assertEqual(summary["excludedInvalidRows"], 3)

    def test_conflicting_duplicate_suppresses_trend(self):
        result = self.execute()
        duplicate = list(result["rows"][0])
        duplicate[5] = -1.4
        result["rows"].append(duplicate)
        summary = summarize_result(result)
        height = next(s for s in summary["series"] if s["variable"] == "H")
        self.assertTrue(height["conflictingDuplicates"])
        self.assertIsNone(height["firstToLastChange"])

    def test_nominal_loop_preserves_two_levels_of_orchestration(self):
        result = self.run_analysis()
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["counts"], {"inferenceDispatches": 3, "toolExecutions": 2})
        self.assertEqual(result["scope"], "hydrological_analysis")
        self.assertFalse(result["analysisResult"]["validation"]["domainValidated"])
        kinds = [e["eventType"] for e in result["trace"]]
        self.assertEqual(kinds.count("DATA_REQUEST_ACCEPTED"), 2)
        self.assertEqual(kinds.count("DATA_OPERATION_COMPLETED"), 2)
        self.assertLess(kinds.index("TOOL_REQUEST_RECEIVED"), kinds.index("SQL_DISPATCHED"))
        self.assertEqual(kinds[-1], "PROBE_FINISHED")

    def test_model_can_choose_history_instead_of_preselected_givry_queries(self):
        provider = ScriptedProvider(["SELECT * FROM flood_analysis.v_hydro_history LIMIT 5"])
        result = self.run_analysis(provider)
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["counts"]["toolExecutions"], 1)
        self.assertEqual(result["analysisResult"]["data"]["rows"][0][0], "F128000101")

    def test_every_inference_contains_catalog_and_per_request_context(self):
        provider = ScriptedProvider([STATION_SQL, OBSERVATIONS_SQL])
        result = self.run_analysis(provider, request_id="REQ-CATALOG", run_id="RUN-CATALOG")
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(len(provider.requests), 3)
        for messages in provider.requests:
            self.assertIn("flood_analysis.v_hydro_history", messages[0]["content"])
            self.assertIn("RUN-CATALOG", messages[0]["content"])
            self.assertIn("captured_real_snapshot", messages[0]["content"])
        self.assertIn("Application-computed context", provider.requests[-1][-1]["content"])

    def test_same_user_requests_have_disjoint_data_operations_and_contexts(self):
        first = self.run_analysis()
        second = self.run_analysis()
        self.assertNotEqual(first["runId"], second["runId"])
        left = {t["operationId"] for t in first["analysisResult"]["toolCalls"]}
        right = {t["operationId"] for t in second["analysisResult"]["toolCalls"]}
        self.assertTrue(left.isdisjoint(right))

    def test_wrong_query_is_not_dispatched(self):
        result = self.run_analysis(ScriptedProvider(["SELECT * FROM private.secret LIMIT 1"]))
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_budget_prevents_a_third_data_operation(self):
        provider = ScriptedProvider([STATION_SQL, OBSERVATIONS_SQL,
                                     "SELECT * FROM flood_analysis.v_hydro_history LIMIT 1"])
        result = self.run_analysis(provider)
        self.assertEqual(result["errorCode"], "ADDITIONAL_TOOL_CALL_NOT_ALLOWED")
        self.assertEqual(result["counts"]["toolExecutions"], 2)

    def test_duplicate_tool_query_is_not_executed_twice(self):
        result = self.run_analysis(ScriptedProvider([OBSERVATIONS_SQL, OBSERVATIONS_SQL]))
        self.assertEqual(result["errorCode"], "DUPLICATE_TOOL_CALL")
        self.assertEqual(result["counts"]["toolExecutions"], 1)

    def test_final_answer_without_receipt_is_retained_with_backend_provenance(self):
        class NoReceipt(ScriptedProvider):
            def complete(self, messages, **kwargs):
                response = super().complete(messages, **kwargs)
                if not response["choices"][0]["message"].get("tool_calls"):
                    response["choices"][0]["message"]["content"] = "Everything is safe."
                return response
        result = self.run_analysis(NoReceipt([OBSERVATIONS_SQL]))
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        analysis = result["analysisResult"]
        self.assertEqual(analysis["answer"], "Everything is safe.")
        self.assertFalse(analysis["validation"]["toolResultReferenced"])
        self.assertTrue(analysis["validation"]["provenanceAttached"])
        self.assertFalse(analysis["validation"]["domainValidated"])
        self.assertEqual(len(analysis["datasets"]), 1)
        self.assertTrue(any("did not cite" in value for value in analysis["uncertainties"]))

    def test_provider_failure_is_not_retried_or_replaced(self):
        provider = Mock(kind="nightshift", route="meterless/auto")
        provider.complete.side_effect = ProviderError("PROVIDER_OUTCOME_UNKNOWN")
        result = self.run_analysis(provider)
        self.assertEqual(result["errorCode"], "PROVIDER_OUTCOME_UNKNOWN")
        self.assertEqual(provider.complete.call_count, 1)
        self.assertEqual(result["counts"]["toolExecutions"], 0)

    def test_empty_result_is_explicit_not_a_fabricated_measurement(self):
        provider = ScriptedProvider([
            "SELECT * FROM flood_analysis.v_hydro_observations WHERE code_station = 'UNKNOWN' LIMIT 5"])
        result = self.run_analysis(provider)
        self.assertEqual(result["status"], "PASSED", result["errorCode"])
        self.assertEqual(result["analysisResult"]["data"]["rows"], [])
        self.assertEqual(result["analysisResult"]["indicators"]["summaries"][0]["series"], [])


if __name__ == "__main__":
    unittest.main()

# History: 2026-10-27: Corrected the malformed-width case while retaining valid finite numeric inputs.

# History: 2026-10-27: Enforced a backend default row cap for admitted SELECTs and traced proposed versus executed SQL.

# History: 2026-10-27: Accepted validated SQL layout and simple OR predicates, retaining strict sources and bounded execution.

# History: 2026-10-27: Added verified station/site context and bounded textual source discovery for model-selected reads.

# History: 2026-10-27: Added explicit workflow 1.3 read attempts, scoped human escalation and backend-linked generated results.

# History: 2026-10-27: Exposed the SQL-verified 2024 weather CSV as catalog data without adding Python weather analysis.
