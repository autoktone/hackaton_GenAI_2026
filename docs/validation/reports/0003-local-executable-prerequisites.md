# 0003 - Local executable prerequisites

- Date: 2026-10-26.
- Result: Partial readiness.
- Git reference: Not recorded.
- World Model source commit: 1742dec56a66e58eef9dda2d2b865823758ca8cd.
- Preconditions: Existing WSL Ubuntu project and read-only checks approved by the project owner.

## Commands and observed results

### Reference instructions

```powershell
wsl.exe -d Ubuntu -- cat /home/info/flood-risk-intelligence/docs/decisions/0010-nightshift-required-integration.md /home/info/flood-risk-intelligence/docs/references/meterless/world-model/upstream/reference/package.json /home/info/flood-risk-intelligence/docs/references/meterless/world-model/upstream/conformance/README.md
```

Exit 0. Reference package 0.1.0 declares no runtime dependencies and uses
development tooling for execution and tests. This is source inspection,
not execution of that reference.

### Node

```powershell
wsl.exe -d Ubuntu -- node --version
```

Expected: Available Node executable. Observed: v22.22.1, exit 0.

### Reference dependencies

```powershell
wsl.exe -d Ubuntu -- test -d /home/info/flood-risk-intelligence/docs/references/meterless/world-model/upstream/reference/node_modules
```

Expected: Exit 0 if that directory exists.
Observed: Exit 1; dependencies are absent at this path.
This is a missing prerequisite, not a failed World Model conformance test.

### Python smoke

```powershell
wsl.exe -d Ubuntu -- python3 -B /home/info/flood-risk-intelligence/smoke_test.py
```

Expected and observed: hello followed by a newline, exit 0.

## Limits and next action

No dependency installation, World Model suite, Nightshift request, or Zetaris
request was performed. No engine integration is established by this report.
A separately approved working copy and dependency installation are needed
before executing the official World Model tests; preserve upstream references.

## History

- 2026-10-26: Recorded authorized local checks and separated smoke success from missing engine prerequisites.
