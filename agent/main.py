"""Explicit CLI for the SELECT-one application integration probe."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys

from agent.analyzer import Analyzer, AnalyzerError
from agent.llm import NightshiftClient, ProviderError, StubProvider, WindowsRuntimeTransport
from agent.orchestrator import Orchestrator, OrchestrationError
from agent.execution_state import ExecutionStateError, ExecutionStateStore
from agent.world_model import BridgeProtocolError, SubprocessTransport, WorldModelClient
from agent.tools_zetaris import SqlError, StubSqlExecutor, ZetarisHttpTransport, ZetarisSettings, ZetarisSqlExecutor


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # Do not echo accidentally supplied secrets from unknown arguments.
        self.exit(2, "CLI_ARGUMENT_ERROR; use --help.\n")


def main(argv=None) -> int:
    parser = SafeParser(description="SELECT-one probe; profiles never fall back automatically.")
    parser.add_argument("--analysis", choices=["select-one", "hydro"], default="select-one")
    parser.add_argument("--snapshot", help="Explicit captured-real snapshot for the hydro stub SQL profile.")
    parser.add_argument("--provider", choices=["stub", "nightshift"], required=True)
    parser.add_argument("--sql-executor", choices=["stub", "zetaris"], required=True)
    parser.add_argument("--transport", choices=["windows-loopback"])
    parser.add_argument("--nightshift-base-url")
    parser.add_argument("--route")
    parser.add_argument("--zetaris-env-file")
    parser.add_argument("--question")
    parser.add_argument("--trace", action="store_true", help="Emit scoped JSON events to stderr.")
    parser.add_argument("--world-model", choices=["disabled", "memory"], default="disabled")
    args = parser.parse_args(argv)
    try:
        if args.analysis == "hydro":
            from agent.hydro import (HydroAnalyzer, HydroSqlExecutor, HydroStubProvider,
                                     SnapshotSqlExecutor, HYDRO_QUESTION)
            from agent.hydro_catalog import HydroQueryPolicy, CATALOG_VERSION, catalog_digest
        if args.provider == "nightshift":
            if not args.nightshift_base_url or not args.route or args.transport != "windows-loopback":
                raise ProviderError("EXPLICIT_NIGHTSHIFT_CONFIGURATION_REQUIRED")
            provider = NightshiftClient(WindowsRuntimeTransport(args.nightshift_base_url),
                                        route=args.route)
        else:
            # Stub profiles do not consult Runtime configuration or token files.
            provider = HydroStubProvider() if args.analysis == "hydro" else StubProvider()
        if args.sql_executor == "zetaris":
            if not args.zetaris_env_file:
                raise SqlError("EXPLICIT_ENV_LOCAL_REQUIRED")
            settings = ZetarisSettings.from_env_file(args.zetaris_env_file)
            if args.analysis == "hydro":
                policy = HydroQueryPolicy()
                executor = HydroSqlExecutor(ZetarisHttpTransport(
                    settings, sql_validator=policy.validate, query_limit=50), policy=policy)
            else:
                executor = ZetarisSqlExecutor(ZetarisHttpTransport(settings))
        else:
            if args.analysis == "hydro":
                snapshot_path = args.snapshot or str(Path(__file__).resolve().parent.parent
                    / "data/snapshots/hubeau-givry-2026-10-27.json")
                executor = SnapshotSqlExecutor.from_file(snapshot_path)
            else:
                executor = StubSqlExecutor()

        def event_sink(event):
            print(json.dumps(event, ensure_ascii=True), file=sys.stderr, flush=True)

        with ExitStack() as stack:
            store = None
            if args.world_model == "memory":
                client = stack.enter_context(WorldModelClient(SubprocessTransport(profile="memory")))
                store = ExecutionStateStore(client,
                    workflow_version="1.3.0" if args.analysis == "hydro" else "1.2.0")
            analyzer = HydroAnalyzer(provider) if args.analysis == "hydro" else Analyzer(provider)
            question = args.question or (HYDRO_QUESTION if args.analysis == "hydro" else
                "Run SELECT 1 AS one and report its value and result receipt.")
            context = ({"catalogVersion": CATALOG_VERSION, "catalogDigest": catalog_digest()}
                       if args.analysis == "hydro" else None)
            result = Orchestrator(analyzer, executor, execution_store=store,
                                  sql_attempts=2 if args.analysis == "hydro" else 1).run(
                question, context=context, event_sink=event_sink if args.trace else None)
            print(json.dumps(result, ensure_ascii=True, indent=2))
            return 0 if result["status"] == "PASSED" else 1
    except (ProviderError, SqlError, AnalyzerError, OrchestrationError, ExecutionStateError) as error:
        print(json.dumps({"status": "FAILED", "errorCode": error.code}))
        return 1
    except BridgeProtocolError:
        print(json.dumps({"status": "FAILED", "errorCode": "WORLD_MODEL_UNAVAILABLE"}))
        return 1
    except Exception:
        print(json.dumps({"status": "FAILED", "errorCode": "UNEXPECTED_APPLICATION_ERROR"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


# History: 2026-10-27: Replaced the placeholder with a scoped CLI selecting provider and SQL executors explicitly.

# History: 2026-10-27: Added explicit memory-engine selection with owned bridge lifecycle and no fallback.

# History: 2026-10-27: Added scoped catalog-aware hydro analysis while retaining the SELECT-one baseline and explicit dependency profiles.

# History: 2026-10-27: Added explicit workflow 1.3 read attempts, scoped human escalation and backend-linked generated results.
