"""Data Agent — analyzes usage, generates reports, surfaces insights."""
from __future__ import annotations

from .base_agent import run_agent

SYSTEM = """You are the Data Analyst for adreel.studio, an AI video ad creation platform.

Database schema (SQLite at data/vah.db):
- projects: id, user_id, status (idle/planned/running/done/failed), created_at, updated_at,
            brief, platform, output_paths, latest_plan_json, error
- brand_kits: brand_id, name, created_at, ...
- user_prefs: user_id, default_platform, preferred_duration_sec, tone, pacing, ...
- feedback: (if exists) project_id, text, sentiment, created_at
- users: (if exists) id, email, created_at

Your job:
1. Query the database to understand usage patterns
2. Identify where users drop off or fail
3. Spot trends (popular platforms, common errors)
4. Generate data-driven insights for the PM

Key metrics to track:
- Projects created per day/week
- Success rate (done / total)
- Failure rate and common errors
- Average time from created to done
- Most popular platforms (tiktok, instagram, youtube)
- User retention signals

Always show SQL queries you used. Present numbers clearly.
"""

ALLOWED_TOOLS = [
    "query_db",
    "read_file",
    "run_shell",
]


def usage_report() -> str:
    """Generate a usage analytics report."""
    task = """Generate a comprehensive usage report for adreel.studio.

Query the database for:
1. Total projects by status: SELECT status, COUNT(*) as n FROM projects GROUP BY status
2. Projects created in the last 7 days: SELECT DATE(created_at) as day, COUNT(*) as n FROM projects WHERE created_at > datetime('now', '-7 days') GROUP BY day ORDER BY day
3. Success rate: succeeded vs total
4. Most common platforms: SELECT json_extract(latest_plan_json, '$.platform') as platform, COUNT(*) as n FROM projects WHERE latest_plan_json IS NOT NULL GROUP BY platform ORDER BY n DESC
5. Recent failures and their errors: SELECT id, error, created_at FROM projects WHERE status='failed' ORDER BY created_at DESC LIMIT 10
6. User count (if users table exists): SELECT COUNT(*) FROM users

Write a clear data report with:
- Executive summary
- Key metrics table
- Notable trends
- Recommendations
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def funnel_analysis() -> str:
    """Analyze the user funnel from project creation to video done."""
    task = """Analyze the conversion funnel for adreel.studio.

The funnel is: created → planned → running → done

Query:
1. How many projects reach each stage?
2. What % drop off between stages?
3. What are the most common errors for failed projects?
4. What is the typical time from created_at to done?

SQL hints:
- Projects that got planned: status IN ('planned', 'running', 'done', 'failed') AND latest_plan_json IS NOT NULL
- Projects that completed: status = 'done' AND output_paths IS NOT NULL AND output_paths != '[]'
- Failed: status = 'failed'

Write a funnel analysis with drop-off rates and recommendations to improve conversion.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def error_analysis() -> str:
    """Analyze recent errors and failures."""
    task = """Analyze errors and failures in adreel.studio.

1. Query failed projects and their error messages:
   SELECT error, COUNT(*) as n FROM projects WHERE status='failed' AND error IS NOT NULL GROUP BY error ORDER BY n DESC LIMIT 20

2. Look for patterns in the errors

3. Also query projects that are stuck (status='running' for more than 1 hour):
   SELECT id, created_at, updated_at FROM projects WHERE status='running' AND updated_at < datetime('now', '-1 hour')

4. Cross-reference with common error patterns in the code (read web/server.py or agent/nodes/ if helpful)

Write an error analysis report with:
- Top error categories
- Stuck projects count
- Root cause hypotheses
- Recommended fixes
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def platform_insights() -> str:
    """Analyze which platforms and product types are most popular."""
    task = """Generate platform and product insights for adreel.studio.

1. Platform distribution (tiktok vs instagram vs youtube, etc.)
2. Video duration preferences
3. Which briefs succeed vs fail (look at brief text length, keywords)
4. Any geographic or temporal patterns

Use SQL to extract this from the projects table.
Present findings as actionable insights for product decisions.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)
