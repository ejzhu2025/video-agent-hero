"""SDE Agent — reads code, implements fixes, commits changes."""
from __future__ import annotations

from .base_agent import run_agent

SYSTEM = """You are a Senior Software Engineer working on adreel.studio, an AI video ad platform.

Tech stack:
- Backend: FastAPI (web/server.py, web/routers/, web/auth/)
- Agent pipeline: LangGraph (agent/nodes/, agent/graph.py)
- Frontend: Single-page app embedded in web/templates.py (HTML/JS/CSS inline)
- DB: SQLite via memory/db.py
- Video render: render/ (FFmpeg + fal.ai T2V/I2V/T2I + Replicate)
- Scraping: web/scrape_product.py
- Landing page: web/landing.py
- Deploy: cloudbuild.yaml → GCP Cloud Run

Key design patterns:
- LangGraph state is a TypedDict — never add non-schema keys; use agent/deps.py for singletons
- Shot rendering priority: (1) user-uploaded image I2V, (2) scraped product I2V, (3) T2I→I2V, (4) T2V
- `show_product=True` on a storyboard entry forces the T2I→I2V path (regenerates scene image from desc)
- HTTP→HTTPS: Cloud Run gets X-Forwarded-Proto header; the app redirects HTTP→HTTPS with 301
- Auth cookie: httponly, samesite=lax, secure=True
- The frontend is one large string in web/templates.py — search for JS functions by name

When fixing a bug:
1. Read relevant files first to understand the current code
2. Make minimal, targeted changes
3. Test your logic (grep for related code, check for edge cases)
4. Commit with a clear user-facing message (no feat:/fix: prefixes in the message body)

IMPORTANT: Only modify files you have read first. Never guess at file contents.
"""

ALLOWED_TOOLS = [
    "read_file",
    "write_file",
    "list_files",
    "grep_code",
    "run_shell",
    "git_log",
    "git_diff",
    "git_commit",
]


def fix_bug(bug_description: str, auto_commit: bool = False) -> str:
    """Investigate and fix a bug in the codebase."""
    commit_instruction = (
        "After making the fix, create a git commit with a clear user-facing message."
        if auto_commit else
        "Show a summary of what you changed but DO NOT commit — the human will review first."
    )
    task = f"""Fix the following bug in adreel.studio:

{bug_description}

Steps:
1. Identify which files are involved (use list_files, grep_code)
2. Read those files carefully
3. Diagnose the root cause
4. Implement the minimal fix
5. {commit_instruction}

Be precise — read files before editing them.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def implement_feature(feature_description: str, auto_commit: bool = False) -> str:
    """Implement a new feature."""
    commit_instruction = (
        "After implementing, create a git commit with a clear user-facing message."
        if auto_commit else
        "Show a summary of changes but DO NOT commit — the human will review first."
    )
    task = f"""Implement the following feature for adreel.studio:

{feature_description}

Steps:
1. Understand the existing codebase structure first (list_files, read relevant files)
2. Plan the implementation (which files to change, what to add)
3. Implement the feature with minimal, focused changes
4. {commit_instruction}
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def code_review(diff_ref: str = "HEAD~1") -> str:
    """Review recent code changes and suggest improvements."""
    task = f"""Review the code changes since {diff_ref}.

1. Get the diff with git_diff
2. Read the changed files to understand context
3. Identify:
   - Bugs or logic errors
   - Security issues
   - Performance problems
   - Missing error handling
   - Code that doesn't match the existing patterns
4. Write a concise code review with specific line references
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def investigate(question: str) -> str:
    """Answer a technical question about the codebase."""
    task = f"""Answer this technical question about the adreel.studio codebase:

{question}

Read the relevant files and give a precise, evidence-based answer.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)
