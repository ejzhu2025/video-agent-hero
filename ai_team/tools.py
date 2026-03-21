"""Shared tools used by all agents."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent


# ── File tools ────────────────────────────────────────────────────────────────

def read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    """Read a file from the project. path is relative to project root."""
    p = PROJECT_ROOT / path
    if not p.exists():
        return f"ERROR: {path} not found"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    chunk = lines[offset: offset + limit]
    result = "\n".join(f"{offset+i+1}: {l}" for i, l in enumerate(chunk))
    total = len(lines)
    if total > offset + limit:
        result += f"\n... ({total - offset - limit} more lines)"
    return result


def write_file(path: str, content: str) -> str:
    """Write content to a file. path is relative to project root."""
    p = PROJECT_ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


def list_files(directory: str = "", pattern: str = "**/*.py") -> str:
    """List files matching a glob pattern."""
    base = PROJECT_ROOT / directory if directory else PROJECT_ROOT
    files = sorted(base.glob(pattern))
    return "\n".join(str(f.relative_to(PROJECT_ROOT)) for f in files[:80])


def grep_code(pattern: str, directory: str = "", file_glob: str = "*.py") -> str:
    """Search for a pattern in code files. Returns matching lines."""
    base = PROJECT_ROOT / directory if directory else PROJECT_ROOT
    result = subprocess.run(
        ["grep", "-rn", "--include", file_glob, pattern, str(base)],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout[:4000] or "(no matches)"


# ── Shell / Cloud tools ───────────────────────────────────────────────────────

def run_shell(cmd: str, cwd: str = "") -> str:
    """Run a shell command. Use sparingly — prefer specific tools."""
    work_dir = str(PROJECT_ROOT / cwd) if cwd else str(PROJECT_ROOT)
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=work_dir,
    )
    out = (result.stdout + result.stderr).strip()
    return out[:3000] or "(no output)"


def get_cloud_run_logs(service: str = "ads-video-hero", lines: int = 50) -> str:
    """Fetch recent Cloud Run logs from GCP."""
    cmd = (
        f"gcloud logging read "
        f"'resource.type=cloud_run_revision AND resource.labels.service_name={service}' "
        f"--limit {lines} --format json --project=$(gcloud config get-value project 2>/dev/null)"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    try:
        entries = json.loads(result.stdout)
        lines_out = []
        for e in entries:
            ts = e.get("timestamp", "")[:19]
            msg = e.get("textPayload") or json.dumps(e.get("jsonPayload", {}))
            sev = e.get("severity", "")
            lines_out.append(f"[{ts}] {sev}: {msg}")
        return "\n".join(lines_out[:50]) or "(no logs)"
    except Exception:
        return result.stdout[:3000]


def get_cloud_run_status(service: str = "ads-video-hero") -> str:
    """Get Cloud Run service status and latest revision info."""
    cmd = f"gcloud run services describe {service} --region us-central1 --format json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    try:
        data = json.loads(result.stdout)
        status = data.get("status", {})
        conditions = status.get("conditions", [])
        traffic = status.get("traffic", [])
        url = status.get("url", "")
        ready = next((c["status"] for c in conditions if c["type"] == "Ready"), "?")
        rev = traffic[0].get("revisionName", "") if traffic else ""
        return f"URL: {url}\nReady: {ready}\nRevision: {rev}"
    except Exception:
        return result.stdout[:2000]


def deploy(message: str = "deploy via AI team") -> str:
    """Trigger a Cloud Build deployment."""
    cmd = f"gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=manual ."
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=300, cwd=str(PROJECT_ROOT),
    )
    return (result.stdout + result.stderr)[-3000:]


# ── HTTP / API test tools ─────────────────────────────────────────────────────

def http_get(url: str, headers: dict | None = None) -> str:
    """Make an HTTP GET request and return status + body."""
    import httpx
    try:
        r = httpx.get(url, headers=headers or {}, timeout=15, follow_redirects=True)
        body = r.text[:2000]
        return f"Status: {r.status_code}\n{body}"
    except Exception as e:
        return f"ERROR: {e}"


def http_post(url: str, json_body: dict, headers: dict | None = None) -> str:
    """Make an HTTP POST request and return status + body."""
    import httpx
    try:
        r = httpx.post(url, json=json_body, headers=headers or {}, timeout=30, follow_redirects=False)
        body = r.text[:2000]
        return f"Status: {r.status_code}\n{body}"
    except Exception as e:
        return f"ERROR: {e}"


# ── DB tools ──────────────────────────────────────────────────────────────────

def query_db(sql: str, db_path: str = "data/vah.db") -> str:
    """Run a read-only SQL query against the SQLite database."""
    import sqlite3
    p = PROJECT_ROOT / db_path
    if not p.exists():
        return f"ERROR: database not found at {db_path}"
    try:
        con = sqlite3.connect(str(p))
        con.row_factory = sqlite3.Row
        cur = con.execute(sql)
        rows = cur.fetchmany(50)
        if not rows:
            return "(no rows)"
        cols = rows[0].keys()
        lines = ["\t".join(cols)]
        for r in rows:
            lines.append("\t".join(str(v) for v in r))
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: {e}"


# ── Git tools ─────────────────────────────────────────────────────────────────

def git_log(n: int = 20) -> str:
    """Show recent git commits."""
    result = subprocess.run(
        ["git", "log", f"-{n}", "--oneline", "--no-merges"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return result.stdout or "(no commits)"


def git_diff(ref: str = "HEAD~1") -> str:
    """Show diff since a ref."""
    result = subprocess.run(
        ["git", "diff", ref], capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return result.stdout[:5000] or "(no diff)"


def git_commit(message: str) -> str:
    """Stage all changes and create a commit."""
    r1 = subprocess.run(["git", "add", "-A"], capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    r2 = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return (r1.stdout + r2.stdout + r2.stderr).strip()


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOL_DEFS = [
    {
        "name": "read_file",
        "description": "Read a file from the project (relative to project root). Optionally specify offset/limit lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path, e.g. web/server.py"},
                "offset": {"type": "integer", "description": "Start line (0-indexed)", "default": 0},
                "limit": {"type": "integer", "description": "Max lines to return", "default": 200},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates parent dirs automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern in the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Subdirectory (empty = root)"},
                "pattern": {"type": "string", "description": "Glob pattern, e.g. **/*.py"},
            },
            "required": [],
        },
    },
    {
        "name": "grep_code",
        "description": "Search for a string/regex in code files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "directory": {"type": "string", "default": ""},
                "file_glob": {"type": "string", "default": "*.py"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command in the project root. Use for installs, tests, linting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string"},
                "cwd": {"type": "string", "description": "Subdirectory to run in", "default": ""},
            },
            "required": ["cmd"],
        },
    },
    {
        "name": "get_cloud_run_logs",
        "description": "Fetch recent Cloud Run logs from GCP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "default": "ads-video-hero"},
                "lines": {"type": "integer", "default": 50},
            },
            "required": [],
        },
    },
    {
        "name": "get_cloud_run_status",
        "description": "Get Cloud Run service health status.",
        "input_schema": {
            "type": "object",
            "properties": {"service": {"type": "string", "default": "ads-video-hero"}},
            "required": [],
        },
    },
    {
        "name": "deploy",
        "description": "Trigger a Cloud Build deployment of the current code.",
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "http_get",
        "description": "Make an HTTP GET request to test a live endpoint.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "headers": {"type": "object"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "http_post",
        "description": "Make an HTTP POST request to test a live endpoint.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "json_body": {"type": "object"},
                "headers": {"type": "object"},
            },
            "required": ["url", "json_body"],
        },
    },
    {
        "name": "query_db",
        "description": "Run a read-only SQL query on the SQLite database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
                "db_path": {"type": "string", "default": "data/vah.db"},
            },
            "required": ["sql"],
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git commits.",
        "input_schema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 20}},
            "required": [],
        },
    },
    {
        "name": "git_diff",
        "description": "Show code diff since a git ref.",
        "input_schema": {
            "type": "object",
            "properties": {"ref": {"type": "string", "default": "HEAD~1"}},
            "required": [],
        },
    },
    {
        "name": "git_commit",
        "description": "Stage all changes and create a git commit.",
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
]

TOOL_MAP: dict[str, Any] = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "grep_code": grep_code,
    "run_shell": run_shell,
    "get_cloud_run_logs": get_cloud_run_logs,
    "get_cloud_run_status": get_cloud_run_status,
    "deploy": deploy,
    "http_get": http_get,
    "http_post": http_post,
    "query_db": query_db,
    "git_log": git_log,
    "git_diff": git_diff,
    "git_commit": git_commit,
}


def execute_tool(name: str, inputs: dict) -> str:
    """Execute a tool by name with the given inputs."""
    fn = TOOL_MAP.get(name)
    if fn is None:
        return f"ERROR: unknown tool '{name}'"
    try:
        return str(fn(**inputs))
    except Exception as e:
        return f"ERROR in {name}: {e}"
