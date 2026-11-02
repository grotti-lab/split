#!/usr/bin/env python3
"""Print how many use cases work, and optionally send each scenario's result to Mycelium.

    python scripts/report_to_mycelium.py                 # summary from .reports/golden.json
    MYCELIUM_TOKEN=myc_... python scripts/report_to_mycelium.py --send --url https://mycelium.example

Reads the results the golden-set run wrote (tests/conftest.py) and the feature ids
from the @feature: tags in .mycelium/specs. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / ".mycelium" / "specs"
RESULTS = ROOT / ".reports" / "golden.json"


def feature_ids() -> dict[str, str]:
    """feature file name -> Mycelium feature id, from the file's @feature: tag."""
    ids = {}
    for path in SPECS.glob("*.feature"):
        for line in path.read_text(encoding="utf-8").splitlines():
            for tag in line.split():
                if tag.startswith("@feature:"):
                    ids[path.name] = tag.split(":", 1)[1]
        ids.setdefault(path.name, path.stem)
    return ids


def commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def send(url: str, token: str, body: dict) -> None:
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/test-runs",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true", help="send each result to Mycelium")
    ap.add_argument("--url", default=os.environ.get("MYCELIUM_URL", "http://localhost:8787"))
    ap.add_argument("--token", default=os.environ.get("MYCELIUM_TOKEN"))
    args = ap.parse_args()

    if not RESULTS.exists():
        sys.exit("No results yet: run make golden first")
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    ids = feature_ids()

    by_feature: dict[str, list[dict]] = {}
    for r in results:
        by_feature.setdefault(ids.get(r["feature_file"], r["feature_file"]), []).append(r)
    working = sum(r["result"] == "pass" for r in results)
    print(f"{working} of {len(results)} use cases work")
    for fid, rs in by_feature.items():
        print(f"  {fid}: {sum(r['result'] == 'pass' for r in rs)} of {len(rs)}")

    if not args.send:
        return
    if not args.token:
        sys.exit("Set MYCELIUM_TOKEN or pass --token")
    sha = commit()
    for fid, rs in by_feature.items():
        for r in rs:
            try:
                send(args.url, args.token, {"feature": fid, "scenario": r["scenario"], "result": r["result"], "commit": sha, "details": r["details"]})
            except urllib.error.HTTPError as e:
                sys.exit(f"Mycelium refused the result for {fid} / {r['scenario']}: {e.code} {e.read().decode()[:200]}")
    print(f"Sent {len(results)} results to {args.url} (commit {sha or 'unknown'})")


if __name__ == "__main__":
    main()
