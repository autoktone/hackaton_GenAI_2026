"""Local judging UI using the existing bounded Analyzer/orchestrator pipeline."""
from __future__ import annotations

from contextlib import ExitStack
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from agent.execution_state import ExecutionStateStore
from agent.hydro import (
    HydroAnalyzer, HydroSqlExecutor, HydroStubProvider, SnapshotSqlExecutor, HYDRO_QUESTION,
)
from agent.hydro_catalog import CATALOG, CATALOG_VERSION, HydroQueryPolicy, catalog_digest
from agent.llm import NightshiftClient, ProviderError, WindowsRuntimeTransport
from agent.main import SafeParser
from agent.orchestrator import Orchestrator, OrchestrationError
from agent.tools_zetaris import SqlError, ZetarisHttpTransport, ZetarisSettings
from agent.world_model import BridgeProtocolError, SubprocessTransport, WorldModelClient

ROOT = Path(__file__).resolve().parents[1]
WEATHER_QUESTION = (
    "For department 44, retrieve five precipitation records from the verified 2024 CSV "
    "in Zetaris. Identify the station and dates, report raw RR and QRR values, and "
    "explain coverage and unit uncertainties. Do not forecast flood risk."
)
WEATHER_SQL = (
    "SELECT * FROM flood_hydro.meteo_precipitations_raw "
    "ORDER BY NUM_POSTE ASC, AAAAMMJJ ASC LIMIT 5"
)
SCENARIOS = [
    {"id": "weather", "name": "Weather records - department 44, 2024", "question": WEATHER_QUESTION},
    {"id": "hydro", "name": "Hydrometry - captured Givry observations", "question": HYDRO_QUESTION},
    {"id": "recovery", "name": "Simulated incident - retry succeeds", "question": WEATHER_QUESTION},
    {"id": "human", "name": "Simulated incident - human intervention", "question": WEATHER_QUESTION},
]


class DemoError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class WeatherSampleProvider:
    """Scripted dependency, explicitly selected in SAMPLE; no inference is generated."""
    kind = "standalone_stub"
    route = "standalone_stub"

    def complete(self, messages, **kwargs):
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if not results:
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_sample_weather", "type": "function",
                "function": {"name": "run_sql", "arguments": json.dumps({"sql": WEATHER_SQL})}}]}
        else:
            message = {"role": "assistant", "content":
                "## Captured weather records\n\n"
                "This SAMPLE replays five actual BLAIN records captured through Zetaris. "
                "The table below is the tool result, not a new live collection.\n\n"
                "The full source was verified separately: 5,490 records and 15 stations "
                "between 2024-01-01 and 2024-12-31. The replay contains only five records.\n\n"
                "RR values are raw: units and accumulation semantics still require source "
                "confirmation. QRR is an uninterpreted source flag. No rainfall calculation, "
                "correlation or flood forecast is produced.\n\n"
                "**Scripted response, not a new Nemotron generation.**\n\n"
                "Evidence receipt: " + results[0]["evidenceId"]}
        return {"model": "standalone_stub", "choices": [{"message": message}]}


class IncidentSampleExecutor:
    """Explicit SAMPLE fault injection; never used in LIVE."""
    kind = "captured_real_snapshot"
    timeout_seconds = 0.0

    def __init__(self, base, *, persistent):
        self.base = base
        self.persistent = persistent
        self.operations = {}

    def prepare_sql(self, sql):
        return self.base.prepare_sql(sql)

    def execute(self, sql, *, operation_id):
        self.operations[operation_id] = self.operations.get(operation_id, 0) + 1
        if self.persistent or self.operations[operation_id] == 1:
            raise SqlError("ZETARIS_TRANSIENT_HTTP_ERROR")
        return self.base.execute(sql, operation_id=operation_id)

    def validate_result(self, result, *, sql, operation_id):
        self.base.validate_result(result, sql=sql, operation_id=operation_id)



class ObservedExecutor:
    """Keep validated result previews per run without placing measurements in World Model."""
    def __init__(self, base):
        self.base = base
        self.results = {}

    def execute(self, sql, *, operation_id):
        result = self.base.execute(sql, operation_id=operation_id)
        self.results[operation_id] = copy.deepcopy(result)
        return result

    def __getattr__(self, name):
        target = getattr(self.base, name)
        if name == "execute_attempt":
            def observed(*args, **kwargs):
                result = target(*args, **kwargs)
                self.results[kwargs["operation_id"]] = copy.deepcopy(result)
                return result
            return observed
        return target


class DemoBackend:
    def __init__(self, *, mode="sample", world_model="disabled",
                 nightshift_base_url=None, route=None, zetaris_env_file=None):
        if mode not in {"sample", "live"} or world_model not in {"disabled", "memory"}:
            raise DemoError("INVALID_DEMO_PROFILE")
        self.mode, self.world_model = mode, world_model
        self._stack = ExitStack()
        self._gate = threading.BoundedSemaphore(1)
        self._last_live = float("-inf")
        self._store = None
        try:
            if mode == "sample":
                self._executor = SnapshotSqlExecutor.from_file(
                    str(ROOT / "data/snapshots/hubeau-givry-2026-10-27.json"))
                self._provider = None
            else:
                if not nightshift_base_url or not route or not zetaris_env_file:
                    raise DemoError("EXPLICIT_LIVE_CONFIGURATION_REQUIRED")
                self._provider = NightshiftClient(WindowsRuntimeTransport(nightshift_base_url), route=route)
                policy = HydroQueryPolicy()
                self._executor = HydroSqlExecutor(ZetarisHttpTransport(
                    ZetarisSettings.from_env_file(zetaris_env_file),
                    sql_validator=policy.validate, query_limit=50), policy=policy)
            if world_model == "memory":
                client = self._stack.enter_context(WorldModelClient(SubprocessTransport(profile="memory")))
                self._store = ExecutionStateStore(client, workflow_version="1.3.0")
        except Exception:
            self._stack.close()
            raise

    def close(self):
        self._stack.close()

    def config(self):
        return {
            "mode": self.mode, "worldModel": self.world_model,
            "inference": "scripted" if self.mode == "sample" else "nightshift",
            "data": "captured_real_snapshot" if self.mode == "sample" else "zetaris_rest",
            "requestedRoute": None if self._provider is None else self._provider.route,
            "scenarios": copy.deepcopy(SCENARIOS if self.mode == "sample" else SCENARIOS[:2]),
            "catalog": copy.deepcopy(CATALOG),
            "limits": {"activeRuns": 1, "logicalSqlReads": 2, "sqlAttempts": 4,
                       "runtimeRequests": 3, "analysisSeconds": 180},
        }

    def run(self, payload, *, event_sink=None, data_sink=None):
        if not isinstance(payload, dict) or set(payload) - {"scenario", "question"}:
            raise DemoError("INVALID_REQUEST")
        scenario = payload.get("scenario", "weather")
        allowed = {item["id"]: item for item in (SCENARIOS if self.mode == "sample" else SCENARIOS[:2])}
        if not isinstance(scenario, str) or scenario not in allowed:
            raise DemoError("SCENARIO_NOT_ALLOWED")
        question = (allowed[scenario]["question"] if self.mode == "sample"
                    else payload.get("question", allowed[scenario]["question"]))
        if (not isinstance(question, str) or not question.strip()
                or len(question.encode("utf-8")) > 512):
            raise DemoError("QUESTION_MUST_BE_1_TO_512_UTF8_BYTES")
        if not self._gate.acquire(blocking=False):
            raise DemoError("DEMO_BUSY")
        try:
            if self.mode == "live":
                if time.monotonic() - self._last_live < 2:
                    raise DemoError("LIVE_RATE_LIMIT")
                self._last_live = time.monotonic()
                provider, executor = self._provider, self._executor
            else:
                provider = HydroStubProvider() if scenario == "hydro" else WeatherSampleProvider()
                executor = (IncidentSampleExecutor(self._executor, persistent=scenario == "human")
                            if scenario in {"human", "recovery"} else self._executor)
            observed = ObservedExecutor(executor)
            def relay(event):
                if event_sink is not None:
                    event_sink(event)
                if event["eventType"] == "DATA_OPERATION_COMPLETED" and data_sink is not None:
                    # The application has validated and recorded completion before this preview.
                    data_sink(copy.deepcopy(observed.results[event["payload"]["operationId"]]))
            result = Orchestrator(HydroAnalyzer(provider), observed, execution_store=self._store,
                                  sql_attempts=2).run(
                question, event_sink=relay,
                context={"catalogVersion": CATALOG_VERSION, "catalogDigest": catalog_digest()})
            return {**result, "question": question, "demoMode": self.mode, "scenario": scenario,
                    "inferenceKind": "scripted" if self.mode == "sample" else "generated",
                    "incidentSimulated": self.mode == "sample" and scenario in {"human", "recovery"}}
        finally:
            self._gate.release()


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, backend):
        self.backend = backend
        super().__init__(address, DemoHandler)


class DemoHandler(BaseHTTPRequestHandler):
    # HTTP/1.0 connection-close framing permits flushed NDJSON progress without a new event service.
    protocol_version = "HTTP/1.0"

    def log_message(self, format, *args):
        # Do not retain client addresses, headers, questions or access tokens.
        pass

    def _allowed_origin(self):
        port = self.server.server_address[1]
        hosts = {"127.0.0.1:" + str(port), "localhost:" + str(port)}
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        return host in hosts and (origin is None or origin in {"http://" + h for h in hosts})

    def _headers(self, status, content_type, length=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                         "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.send_header("Connection", "close")
        self.end_headers()

    def _json(self, status, body):
        data = json.dumps(body, ensure_ascii=True, allow_nan=False).encode()
        self._headers(status, "application/json; charset=utf-8", len(data))
        self.wfile.write(data)

    def do_GET(self):
        if not self._allowed_origin():
            return self._json(403, {"errorCode": "LOCAL_ORIGIN_REQUIRED"})
        if self.path == "/":
            data = (ROOT / "web/index.html").read_bytes()
            self._headers(200, "text/html; charset=utf-8", len(data))
            self.wfile.write(data)
        elif self.path == "/api/config":
            self._json(200, self.server.backend.config())
        else:
            self._json(404, {"errorCode": "NOT_FOUND"})

    def do_POST(self):
        if not self._allowed_origin():
            return self._json(403, {"errorCode": "LOCAL_ORIGIN_REQUIRED"})
        if self.path != "/api/analyze":
            return self._json(404, {"errorCode": "NOT_FOUND"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self._json(415, {"errorCode": "JSON_REQUIRED"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            return self._json(400, {"errorCode": "INVALID_REQUEST"})

        started = False
        disconnected = False
        def stream(item):
            nonlocal started, disconnected
            if disconnected:
                return
            try:
                if not started:
                    self._headers(200, "application/x-ndjson; charset=utf-8")
                    started = True
                self.wfile.write((json.dumps(item, ensure_ascii=True, allow_nan=False) + "\n").encode())
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                # Browser progress is best-effort; the authoritative run trace remains in the backend.
                disconnected = True
        try:
            result = self.server.backend.run(payload,
                event_sink=lambda event: stream({"type": "event", "event": event}),
                data_sink=lambda data: stream({"type": "data", "data": data}))
            stream({"type": "result", "result": result})
        except DemoError as error:
            if not started:
                self._json(429 if error.code in {"DEMO_BUSY", "LIVE_RATE_LIMIT"} else 400,
                           {"errorCode": error.code})
            else:
                stream({"type": "error", "errorCode": error.code})
        except Exception:
            if not started:
                self._json(500, {"errorCode": "DEMO_REQUEST_FAILED"})
            else:
                stream({"type": "error", "errorCode": "DEMO_REQUEST_FAILED"})


def main(argv=None):
    parser = SafeParser(description="Local evidence explorer; SAMPLE never contacts live platforms.")
    parser.add_argument("--mode", choices=["sample", "live"], default="sample")
    parser.add_argument("--world-model", choices=["disabled", "memory"], default="disabled")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--nightshift-base-url")
    parser.add_argument("--route")
    parser.add_argument("--zetaris-env-file")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("Invalid port.")
    backend = None
    server = None
    try:
        backend = DemoBackend(mode=args.mode, world_model=args.world_model,
                              nightshift_base_url=args.nightshift_base_url,
                              route=args.route, zetaris_env_file=args.zetaris_env_file)
        server = DemoServer(("127.0.0.1", args.port), backend)
        print("Flood Risk Decision Intelligence: http://127.0.0.1:" + str(server.server_port),
              flush=True)
        print("Mode=" + args.mode + "; WorldModel=" + args.world_model
              + "; local access only; stop with Ctrl+C.", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (DemoError, SqlError, ProviderError, OrchestrationError) as error:
        print(json.dumps({"status": "FAILED", "errorCode": error.code}))
        return 1
    except (BridgeProtocolError, OSError):
        print(json.dumps({"status": "FAILED", "errorCode": "DEMO_STARTUP_FAILED"}))
        return 1
    finally:
        if server is not None:
            server.server_close()
        if backend is not None:
            backend.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# History: 2026-10-27: Rejected non-string scenario values before dispatch.
