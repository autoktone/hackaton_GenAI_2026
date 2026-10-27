"""Credential-free SAMPLE and local HTTP streaming checks; live transports are blocked."""
from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from agent.demo import DemoBackend, DemoError, DemoServer


class DemoBackendTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("agent.demo.ZetarisSettings.from_env_file",
                                side_effect=AssertionError("Private configuration forbidden.")))
        self.enterContext(patch("agent.demo.WindowsRuntimeTransport.post",
                                side_effect=AssertionError("Live inference forbidden.")))
        self.enterContext(patch("agent.demo.SubprocessTransport",
                                side_effect=AssertionError("Native process forbidden in portable SAMPLE.")))
        self.backend = DemoBackend(
            nightshift_base_url="DO_NOT_EXPOSE_RUNTIME", route="DO_NOT_EXPOSE_ROUTE",
            zetaris_env_file="/DO_NOT_READ/.env.local")
        self.addCleanup(self.backend.close)

    def test_sample_weather_has_real_captured_rows_and_discloses_scripted_inference(self):
        result = self.backend.run({"scenario":"weather", "question":"Ignored custom SAMPLE question"})
        self.assertEqual(result["status"],"PASSED",result["errorCode"])
        self.assertEqual(result["demoMode"],"sample")
        self.assertEqual(result["inferenceKind"],"scripted")
        self.assertFalse(result["worldModelUsed"])
        self.assertEqual(result["profile"]["sourceKind"],"captured_real_snapshot")
        self.assertEqual(result["analysisResult"]["datasets"][0]["rows"][0],
                         [44015001,"BLAIN",47.472833,-1.771667,20240101,37.6,1])
        self.assertIn("Scripted response",result["analysisResult"]["answer"])
        self.assertFalse(result["analysisResult"]["validation"]["domainValidated"])

    def test_data_preview_follows_recorded_completion_and_precedes_next_inference(self):
        order = []
        self.backend.run({"scenario":"weather"},
            event_sink=lambda event:order.append(("event",event["eventType"])),
            data_sink=lambda data:order.append(("data",data["rowCount"])))
        completed=order.index(("event","DATA_OPERATION_COMPLETED"))
        preview=order.index(("data",5))
        later=[index for index,item in enumerate(order)
               if item==("event","INFERENCE_DISPATCHED") and index>preview]
        self.assertLess(completed,preview)
        self.assertTrue(later)

    def test_hydrometry_uses_the_shared_pipeline(self):
        result=self.backend.run({"scenario":"hydro"})
        self.assertEqual(result["status"],"PASSED",result["errorCode"])
        self.assertEqual(result["counts"]["toolExecutions"],2)
        self.assertEqual(len(result["analysisResult"]["datasets"]),2)

    def test_explicit_recovery_scenario_traces_a_retry(self):
        result=self.backend.run({"scenario":"recovery"})
        self.assertEqual(result["status"],"PASSED",result["errorCode"])
        self.assertTrue(result["incidentSimulated"])
        self.assertEqual(result["counts"]["sqlAttempts"],2)
        self.assertEqual(result["counts"]["toolExecutions"],1)
        self.assertIn("SQL_RETRY_SCHEDULED",[e["eventType"] for e in result["trace"]])

    def test_human_scenario_stops_without_additional_inference(self):
        result=self.backend.run({"scenario":"human"})
        self.assertEqual(result["status"],"WAITING_HUMAN")
        self.assertEqual(result["counts"]["inferenceDispatches"],1)
        self.assertEqual(result["counts"]["sqlAttempts"],2)
        self.assertEqual(result["humanIntervention"]["runId"],result["runId"])

    def test_sample_configuration_does_not_expose_unused_live_settings(self):
        config=self.backend.config()
        serialized=json.dumps(config)
        self.assertNotIn("DO_NOT_",serialized)
        self.assertEqual(config["worldModel"],"disabled")
        self.assertEqual(len(config["scenarios"]),4)
        self.assertEqual(config["catalog"]["precipitationCoverage"]["verifiedRows"],5490)

    def test_live_requires_explicit_configuration_and_never_falls_back(self):
        with self.assertRaises(DemoError) as caught:
            DemoBackend(mode="live")
        self.assertEqual(caught.exception.code,"EXPLICIT_LIVE_CONFIGURATION_REQUIRED")

    def test_invalid_scenario_and_extra_request_fields_are_rejected(self):
        for payload in [{"scenario":"unknown"},{"scenario":{}},{"scenario":"weather","token":"not-accepted"},[]]:
            with self.subTest(payload=payload),self.assertRaises(DemoError):
                self.backend.run(payload)

    def test_simultaneous_runs_are_admission_limited_without_context_reuse(self):
        self.backend._gate.acquire()
        try:
            with self.assertRaises(DemoError) as caught:
                self.backend.run({"scenario":"weather"})
            self.assertEqual(caught.exception.code,"DEMO_BUSY")
        finally:
            self.backend._gate.release()
        first=self.backend.run({"scenario":"weather"})
        second=self.backend.run({"scenario":"weather"})
        self.assertNotEqual(first["runId"],second["runId"])
        self.assertNotEqual(first["requestId"],second["requestId"])


class DemoHttpTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("agent.demo.WindowsRuntimeTransport.post",
                                side_effect=AssertionError("No live inference.")))
        self.enterContext(patch("agent.demo.ZetarisHttpTransport.post_query",
                                side_effect=AssertionError("No live SQL.")))
        self.enterContext(patch("agent.demo.SubprocessTransport",
                                side_effect=AssertionError("No Node in portable HTTP checks.")))
        self.backend=DemoBackend()
        self.server=DemoServer(("127.0.0.1",0),self.backend)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup_server)
        self.base="http://127.0.0.1:"+str(self.server.server_port)

    def cleanup_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.backend.close()

    def request(self,path,body=None,headers=None):
        data=None if body is None else body.encode()
        return urlopen(Request(self.base+path,data=data,headers=headers or {}),timeout=10)

    def test_html_and_safe_configuration_are_served(self):
        with self.request("/") as response:
            html=response.read().decode()
            self.assertEqual(response.status,200)
            self.assertIn('lang="en"',html)
            self.assertIn("Execution trace",html)
            self.assertLess(html.index("Application control and agent loop"),
                            html.index('id="analysisHeading"'))
            self.assertLess(html.index('id="analysisHeading"'),html.index("Returned data"))
            self.assertIn("Scientific interpretation: NOT VALIDATED",html)
            self.assertIn("Scripted SAMPLE response - no live Nemotron inference.",html)
            self.assertIn('id="executionStatus"',html)
            self.assertIn('id="analysisQuestion"',html)
            self.assertIn("Human intervention is required",html)
            self.assertIn('aria-live="polite"',html)
            self.assertEqual(response.headers["Cache-Control"],"no-store")
        with self.request("/api/config") as response:
            self.assertEqual(json.load(response)["mode"],"sample")

    def test_post_streams_events_and_validated_rows_before_final_result(self):
        with self.request("/api/analyze",'{"scenario":"weather"}',
                          {"Content-Type":"application/json"}) as response:
            self.assertEqual(response.headers.get_content_type(),"application/x-ndjson")
            items=[json.loads(line) for line in response if line.strip()]
        self.assertEqual(items[0]["type"],"event")
        self.assertEqual(items[-1]["type"],"result")
        preview=next(i for i,item in enumerate(items) if item["type"]=="data")
        self.assertLess(preview,len(items)-1)
        self.assertEqual(items[preview]["data"]["rows"][0][1],"BLAIN")
        self.assertEqual(items[-1]["result"]["status"],"PASSED")

    def test_secrets_paths_are_not_exposed(self):
        for path in ["/.env","/.env.local","/agent/demo.py","/../.env"]:
            with self.subTest(path=path),self.assertRaises(HTTPError) as caught:
                self.request(path)
            self.assertEqual(caught.exception.code,404)
            caught.exception.close()

    def test_foreign_origin_cannot_dispatch_work(self):
        with patch.object(self.backend,"run",side_effect=AssertionError("Must not dispatch.")) as dispatch:
            with self.assertRaises(HTTPError) as caught:
                self.request("/api/analyze",'{"scenario":"weather"}',
                    {"Content-Type":"application/json","Origin":"https://untrusted.example"})
            self.assertEqual(caught.exception.code,403)
            caught.exception.close()
            dispatch.assert_not_called()

    def test_unsupported_content_and_invalid_json_are_rejected(self):
        for body,headers,status in [
            ('{"scenario":"weather"}',{"Content-Type":"text/plain"},415),
            ('{',{"Content-Type":"application/json"},400),
        ]:
            with self.subTest(status=status),self.assertRaises(HTTPError) as caught:
                self.request("/api/analyze",body,headers)
            self.assertEqual(caught.exception.code,status)
            caught.exception.close()

    def test_busy_is_reported_without_starting_another_run(self):
        self.backend._gate.acquire()
        try:
            with self.assertRaises(HTTPError) as caught:
                self.request("/api/analyze",'{"scenario":"weather"}',
                             {"Content-Type":"application/json"})
            self.assertEqual(caught.exception.code,429)
            self.assertEqual(json.loads(caught.exception.read())["errorCode"],"DEMO_BUSY")
            caught.exception.close()
        finally:
            self.backend._gate.release()


if __name__=="__main__":
    unittest.main()

# History: 2026-10-27: Covered malformed scenario values and closed HTTP test responses explicitly.

# History: 2026-10-27: Checked prominent result placement, separate validation status, and explicit SAMPLE/incident disclosure.
