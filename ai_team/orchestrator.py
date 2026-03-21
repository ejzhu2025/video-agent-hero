"""
AI Team Orchestrator for adreel.studio
=======================================
Usage:
  python -m ai_team.orchestrator <command> [args]

Commands:
  health              Full health check (QA + DevOps)
  weekly              Weekly report (PM + Data)
  insights            PM insights: auto-discover UX issues + draft stories
  bug "<description>" Analyze + fix a bug (PM triage → SDE fix)
  feature "<desc>"    Implement a feature (PM plan → SDE implement)
  deploy [reason]     Deploy current code (DevOps)
  data                Usage analytics report
  funnel              Conversion funnel analysis
  errors              Error analysis
  review              Code review of recent changes
  test [url]          Run QA regression test (optionally test scrape with url)
  ask "<question>"    Ask SDE a codebase question

Example:
  python -m ai_team.orchestrator health
  python -m ai_team.orchestrator bug "Changelog shows stale data"
  python -m ai_team.orchestrator weekly
"""
from __future__ import annotations

import os
import sys
import textwrap
from datetime import datetime


def _require_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        print("Export it: export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)


def _print_result(agent: str, result: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*70}")
    print(f"  {agent}  [{now}]")
    print(f"{'='*70}\n")
    print(result)
    print()


def cmd_health():
    """Run full health check."""
    _require_api_key()
    from .qa_agent import health_check
    from .devops_agent import check_health

    print("Running QA health check...")
    qa_result = health_check()
    _print_result("QA Agent — Health Check", qa_result)

    print("Running DevOps health check...")
    devops_result = check_health()
    _print_result("DevOps Agent — Infrastructure", devops_result)


def cmd_weekly():
    """Generate weekly report."""
    _require_api_key()
    from .pm_agent import weekly_report
    from .data_agent import usage_report

    print("Generating PM weekly report...")
    pm_result = weekly_report()
    _print_result("PM Agent — Weekly Report", pm_result)

    print("Generating data analytics...")
    data_result = usage_report()
    _print_result("Data Agent — Analytics", data_result)


def cmd_bug(description: str, auto_fix: bool = False):
    """Triage and fix a bug."""
    _require_api_key()
    from .pm_agent import analyze_feedback
    from .sde_agent import fix_bug

    print(f"PM triaging: {description[:60]}...")
    triage = analyze_feedback(description)
    _print_result("PM Agent — Triage", triage)

    print("SDE investigating fix...")
    fix = fix_bug(description, auto_commit=auto_fix)
    _print_result("SDE Agent — Fix", fix)


def cmd_feature(description: str, auto_commit: bool = False):
    """Plan and implement a feature."""
    _require_api_key()
    from .pm_agent import create_sprint_plan
    from .sde_agent import implement_feature

    print(f"PM planning feature: {description[:60]}...")
    plan = create_sprint_plan(description)
    _print_result("PM Agent — Sprint Plan", plan)

    print("SDE implementing feature...")
    impl = implement_feature(description, auto_commit=auto_commit)
    _print_result("SDE Agent — Implementation", impl)


def cmd_deploy(reason: str = "manual deploy"):
    """Deploy current code."""
    _require_api_key()
    from .devops_agent import trigger_deploy

    print(f"DevOps deploying: {reason}")
    result = trigger_deploy(reason)
    _print_result("DevOps Agent — Deploy", result)


def cmd_data():
    """Usage analytics."""
    _require_api_key()
    from .data_agent import usage_report
    result = usage_report()
    _print_result("Data Agent — Usage Report", result)


def cmd_funnel():
    """Funnel analysis."""
    _require_api_key()
    from .data_agent import funnel_analysis
    result = funnel_analysis()
    _print_result("Data Agent — Funnel Analysis", result)


def cmd_errors():
    """Error analysis."""
    _require_api_key()
    from .data_agent import error_analysis
    result = error_analysis()
    _print_result("Data Agent — Error Analysis", result)


def cmd_review():
    """Code review."""
    _require_api_key()
    from .sde_agent import code_review
    result = code_review()
    _print_result("SDE Agent — Code Review", result)


def cmd_test(scrape_url: str | None = None):
    """QA regression test."""
    _require_api_key()
    from .qa_agent import regression_test, test_scrape

    result = regression_test()
    _print_result("QA Agent — Regression Test", result)

    if scrape_url:
        result2 = test_scrape(scrape_url)
        _print_result("QA Agent — Scrape Test", result2)


def cmd_insights(date: str | None = None):
    """Run PM insights: auto-discover UX issues + draft user stories."""
    from .pm_insights import run as run_pm_insights
    path = run_pm_insights(date_str=date)
    if path:
        print(f"\nReport saved to: {path}")


def cmd_ask(question: str):
    """Ask SDE a codebase question."""
    _require_api_key()
    from .sde_agent import investigate
    result = investigate(question)
    _print_result("SDE Agent — Answer", result)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = args[0]
    rest = args[1:]

    COMMANDS = {
        "health":    (cmd_health, []),
        "weekly":    (cmd_weekly, []),
        "insights":  (cmd_insights, []),
        "bug":       (cmd_bug, ["description"]),
        "feature":   (cmd_feature, ["description"]),
        "deploy":    (cmd_deploy, []),
        "data":      (cmd_data, []),
        "funnel":    (cmd_funnel, []),
        "errors":    (cmd_errors, []),
        "review":    (cmd_review, []),
        "test":      (cmd_test, []),
        "ask":       (cmd_ask, ["question"]),
    }

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)

    fn, params = COMMANDS[cmd]

    if params and not rest:
        print(f"Usage: python -m ai_team.orchestrator {cmd} \"<{params[0]}>\"")
        sys.exit(1)

    if rest:
        fn(rest[0])
    else:
        fn()


if __name__ == "__main__":
    main()
