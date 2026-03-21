"""PM Agent — analyzes feedback, triages bugs, creates weekly reports."""
from __future__ import annotations

from .base_agent import run_agent

SYSTEM = """You are the Product Manager for adreel.studio, an AI-powered short-video ad creation platform.

Your responsibilities:
1. Analyze user feedback and bug reports
2. Triage issues by severity (P0=down, P1=major, P2=minor, P3=nice-to-have)
3. Create actionable task lists for the engineering team
4. Write weekly product update reports
5. Check the database to understand user behavior and trends

Platform overview:
- Users provide a product URL → AI scrapes it → generates a video ad plan → renders video
- Stack: FastAPI + LangGraph + Google Gemini (planning) + fal.ai or Replicate (video gen)
- Deployed on Cloud Run at https://adreel.studio
- Auth: Google OAuth + guest codes
- Billing: Stripe

When analyzing bugs, consider:
- Is the service up? Check Cloud Run status
- Are there error patterns in logs?
- How many users are affected?
- What is the user impact?

Output format for task lists:
## Triage Report — <date>

### P0 (Critical — fix now)
- [ ] <issue>: <impact> — Assigned to: SDE

### P1 (High — fix this sprint)
- [ ] <issue>: <impact>

### P2 (Medium — backlog)
- [ ] <issue>

### Insights
<key observations>
"""

ALLOWED_TOOLS = [
    "get_cloud_run_status",
    "get_cloud_run_logs",
    "query_db",
    "http_get",
    "git_log",
    "read_file",
    "list_files",
]


def analyze_feedback(feedback: str) -> str:
    """Analyze user feedback and produce a triage report."""
    task = f"""A user reported the following issue:

{feedback}

Please:
1. Check Cloud Run status to see if the service is up
2. Check recent logs for related errors
3. Query the database to understand the scope (how many users affected)
4. Review the git log to see if recent changes might have caused this
5. Produce a triage report with severity, root cause hypothesis, and recommended fix
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def weekly_report() -> str:
    """Generate a weekly product status report."""
    task = """Generate a weekly product status report for adreel.studio.

Please:
1. Check Cloud Run status and recent logs for any errors/anomalies
2. Query the database:
   - SELECT COUNT(*), status FROM projects GROUP BY status
   - SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 days') (if table exists)
   - SELECT COUNT(*) FROM feedback WHERE created_at > datetime('now', '-7 days') (if table exists)
3. Check git log for what was shipped this week
4. Write a clear weekly report covering:
   - 🟢/🟡/🔴 Service health
   - New users this week
   - Videos generated this week
   - Key bugs fixed
   - What's coming next
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def create_sprint_plan(goals: str) -> str:
    """Create a sprint plan based on stated goals."""
    task = f"""Create a 1-week sprint plan for adreel.studio.

Goals/context from founder:
{goals}

Please:
1. Review git log to understand recent work
2. Check current Cloud Run status
3. Query DB for any data that helps prioritize
4. Create a clear sprint plan with specific tasks, priorities, and success criteria
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)
