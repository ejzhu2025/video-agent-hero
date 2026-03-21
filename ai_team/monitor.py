"""ai_team/monitor.py — Background log monitor for adreel.studio.

Polls Cloud Run logs every N minutes, detects errors, and triggers DevOps analysis.

Usage:
    python -m ai_team.monitor            # run forever (default: every 5 min)
    python -m ai_team.monitor --once     # single scan, exit
    python -m ai_team.monitor --interval 15  # every 15 min
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta


PROJECT = "adreel-490423"
SERVICE = "ads-video-hero"
REGION = "us-central1"

# Patterns that indicate real errors (not just noise)
ERROR_PATTERNS = [
    "ERROR",
    "CRITICAL",
    "Traceback",
    "Exception",
    "exit code 1",
    "OOM",
    "Out of memory",
    "connection refused",
    "timeout",
    "500 Internal Server Error",
]

# Patterns to ignore (known non-issues)
IGNORE_PATTERNS = [
    "DeprecationWarning",
    "OPTIONS /api/projects HTTP/1.1\" 400",  # CORS preflight from unknown origin
    "404 Not Found",  # favicon etc
]


def _ts_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_logs(since_minutes: int = 10) -> list[str]:
    """Fetch Cloud Run logs from the last N minutes."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    cmd = [
        "gcloud", "logging", "read",
        f'resource.type="cloud_run_revision" AND resource.labels.service_name="{SERVICE}"'
        f' AND timestamp>="{since}"',
        f"--project={PROJECT}",
        "--limit=200",
        "--format=json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"[monitor] gcloud error: {result.stderr[:200]}", file=sys.stderr)
            return []
        entries = json.loads(result.stdout or "[]")
        lines = []
        for e in entries:
            text = e.get("textPayload") or e.get("jsonPayload", {}).get("message", "")
            if text:
                lines.append(text)
        return lines
    except Exception as ex:
        print(f"[monitor] fetch_logs failed: {ex}", file=sys.stderr)
        return []


def _is_error(line: str) -> bool:
    low = line.lower()
    if any(p.lower() in low for p in IGNORE_PATTERNS):
        return False
    return any(p.lower() in low for p in ERROR_PATTERNS)


def _analyze_errors(errors: list[str]) -> str:
    """Run the DevOps agent to analyze errors, or return a simple summary."""
    if not errors:
        return ""

    # Try to use DevOps agent for analysis
    try:
        from .devops_agent import check_health
        summary = check_health()
        return summary
    except Exception:
        # Fallback: simple text summary
        return "\n".join(errors[:20])


def scan_once(since_minutes: int = 10, verbose: bool = True) -> dict:
    """Do a single log scan. Returns {errors: [...], healthy: bool}."""
    ts = _ts_now()
    if verbose:
        print(f"[{ts}] Scanning last {since_minutes}min of logs...")

    lines = _fetch_logs(since_minutes)
    errors = [l for l in lines if _is_error(l)]

    result = {
        "timestamp": ts,
        "lines_scanned": len(lines),
        "errors_found": len(errors),
        "errors": errors[:10],  # top 10
        "healthy": len(errors) == 0,
    }

    if verbose:
        if errors:
            print(f"[{ts}] *** {len(errors)} errors detected ***")
            for e in errors[:5]:
                print(f"  {e[:120]}")
        else:
            print(f"[{ts}] OK — {len(lines)} log lines, no errors")

    return result


def run_monitor(interval_minutes: int = 5, verbose: bool = True):
    """Run the monitor loop indefinitely."""
    print(f"[monitor] Starting — polling every {interval_minutes}min")
    print(f"[monitor] Service: {PROJECT}/{SERVICE} ({REGION})")

    consecutive_errors = 0

    while True:
        result = scan_once(since_minutes=interval_minutes + 1, verbose=verbose)

        if not result["healthy"]:
            consecutive_errors += 1
            print(f"[monitor] Running DevOps analysis (consecutive error windows: {consecutive_errors})...")
            try:
                analysis = _analyze_errors(result["errors"])
                if analysis:
                    print("--- DevOps Analysis ---")
                    print(analysis[:1000])
                    print("---")
            except Exception as ex:
                print(f"[monitor] Analysis failed: {ex}")
        else:
            consecutive_errors = 0

        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="adreel.studio log monitor")
    parser.add_argument("--once", action="store_true", help="Single scan then exit")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in minutes (default: 5)")
    parser.add_argument("--since", type=int, default=10, help="Look back N minutes for --once mode")
    parser.add_argument("--quiet", action="store_true", help="Less output")
    args = parser.parse_args()

    if args.once:
        result = scan_once(since_minutes=args.since, verbose=not args.quiet)
        if not result["healthy"] and not args.quiet:
            print("\nRunning DevOps analysis...")
            analysis = _analyze_errors(result["errors"])
            if analysis:
                print(analysis)
        sys.exit(0 if result["healthy"] else 1)
    else:
        run_monitor(interval_minutes=args.interval, verbose=not args.quiet)


if __name__ == "__main__":
    main()
