"""Restore the pinned official World Model files from versioned, verified references.

This script never downloads packages or overwrites local modifications.
Run without --apply to inspect the copy plan. Dependencies are a separate npm ci.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "1742dec56a66e58eef9dda2d2b865823758ca8cd"


def prepare(*, apply=False):
    references = ROOT / "docs/references/meterless/world-model"
    manifest = json.loads((references / "provenance.json").read_text(encoding="utf-8"))
    if manifest.get("commit") != COMMIT:
        raise RuntimeError("Unexpected upstream revision; review provenance before installation.")
    target = ROOT / "vendor/meterless/world-model"
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Runtime path must remain inside the project.")
    plan = []
    for entry in manifest["files"]:
        original = PurePosixPath(entry["original_path"])
        relative = original.relative_to("engines/world-model")
        if ".." in relative.parts:
            raise RuntimeError("Unsafe reference path.")
        if relative.name == "AGENTS.md":
            relative = relative.with_name("agents-spec.md")
        local = references / entry["local_path"]
        destination = target / str(relative)
        if (not local.resolve().is_relative_to(references.resolve())
                or not destination.resolve().is_relative_to(target.resolve())):
            raise RuntimeError("Reference path is outside its allowed directory.")
        data = local.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise RuntimeError("Reference fingerprint mismatch: " + str(relative))
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != entry["sha256"]:
                raise RuntimeError("Local modification preserved; installation stopped: " + str(relative))
        else:
            plan.append((destination, data))
    # All sources and existing destinations are verified before any write.
    if apply:
        for destination, data in plan:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(data)
    return {"commit": COMMIT, "verifiedFiles": len(manifest["files"]),
            "missingFiles": len(plan), "copiedFiles": len(plan) if apply else 0,
            "applied": apply, "dependenciesInstalled": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Copy missing verified reference files into ignored vendor/.")
    args = parser.parse_args(argv)
    try:
        result = prepare(apply=args.apply)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print("PREPARATION_FAILED: " + str(error))
        return 1
    print(json.dumps(result, indent=2))
    if not args.apply:
        print("Dry run only. Use --apply to copy missing verified files.")
    print("Then run: npm --prefix vendor/meterless/world-model/reference ci --include=dev --no-audit --no-fund")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
