# AI Team — adreel.studio

A multi-agent AI team that helps run adreel.studio autonomously.

## Agents

| Agent | Role | Key capabilities |
|-------|------|-----------------|
| **PM Agent** | Product Manager | Analyze feedback, triage bugs, write sprint plans & weekly reports |
| **SDE Agent** | Senior Engineer | Read/write code, fix bugs, implement features, code review |
| **QA Agent** | QA Engineer | Test live API, health checks, write bug reports |
| **DevOps Agent** | Infrastructure | Monitor Cloud Run, check logs, trigger deploys |
| **Data Agent** | Data Analyst | Query DB, funnel analysis, error trends, usage reports |

## Setup

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Install anthropic SDK (already in requirements)
pip install anthropic httpx
```

## Usage

```bash
cd /Users/bytedance/Desktop/ads_video_hero

# Health check (QA + DevOps)
python -m ai_team health

# Weekly report (PM + Data)
python -m ai_team weekly

# Investigate & fix a bug
python -m ai_team bug "Users see 'fail to fetch' when clicking Approve"

# Implement a feature
python -m ai_team feature "Add a progress bar during video generation"

# Code review recent changes
python -m ai_team review

# Data analytics
python -m ai_team data
python -m ai_team funnel
python -m ai_team errors

# QA regression test
python -m ai_team test
python -m ai_team test "https://www.amazon.com/dp/B08H75RTZ8"

# Ask a codebase question
python -m ai_team ask "How does the I2V rendering pipeline work?"

# Deploy
python -m ai_team deploy "hotfix for auth bug"
```

## Architecture

```
orchestrator.py       CLI entry point — routes commands to agents
├── pm_agent.py       Uses: Cloud Run status, logs, DB, git log
├── sde_agent.py      Uses: read/write files, grep, shell, git
├── qa_agent.py       Uses: HTTP requests, Cloud Run logs, code read
├── devops_agent.py   Uses: Cloud Run status/logs, shell, deploy
├── data_agent.py     Uses: SQLite DB queries
├── base_agent.py     Agentic loop (Anthropic SDK tool use)
└── tools.py          All tool implementations + definitions
```

Each agent runs an agentic loop: Claude calls tools (read files, query DB, make HTTP requests, etc.) until it has enough information to produce a final answer.

## Use in Python

```python
from ai_team.pm_agent import analyze_feedback, weekly_report
from ai_team.sde_agent import fix_bug, investigate
from ai_team.qa_agent import health_check, regression_test
from ai_team.devops_agent import check_health
from ai_team.data_agent import usage_report, funnel_analysis

# Analyze a user complaint
report = analyze_feedback("The video generation always fails with 500 error")
print(report)

# Get weekly metrics
report = weekly_report()
print(report)
```
