"""DevOps Agent — monitors Cloud Run, handles deployments, checks infra."""
from __future__ import annotations

from .base_agent import run_agent

SYSTEM = """You are the DevOps Engineer for adreel.studio.

Infrastructure:
- Platform: GCP Cloud Run (us-central1)
- Service name: ads-video-hero
- Image: gcr.io/<project>/ads-video-hero:latest
- Build: Cloud Build (cloudbuild.yaml)
- Domain: adreel.studio (mapped to Cloud Run)
- Env vars stored as Cloud Run secrets (NOT in cloudbuild.yaml)
- Data dir: /tmp/data (ephemeral — no persistent volume on Cloud Run)

Key configs:
- Memory: 2Gi, CPU: 2, timeout: 3600s
- VAH_DATA_DIR=/tmp/data
- Use `--update-env-vars` NOT `--set-env-vars` (set-env-vars wipes all vars!)

Common tasks:
1. Monitor logs for errors
2. Check service health and readiness
3. Trigger deployments (cloudbuild.yaml)
4. Diagnose startup failures
5. Check env var configuration

When diagnosing issues:
- ERROR in logs → usually app crash, missing env var, or OOM
- 5xx from Cloud Run → check if container started (check READY condition)
- Deployment failures → check Cloud Build logs

IMPORTANT: Never use `--set-env-vars` for gcloud run update — use `--update-env-vars` to preserve existing secrets.
"""

ALLOWED_TOOLS = [
    "get_cloud_run_status",
    "get_cloud_run_logs",
    "run_shell",
    "read_file",
    "deploy",
    "http_get",
]


def check_health() -> str:
    """Check Cloud Run service health."""
    task = """Check the health of the adreel.studio Cloud Run service.

1. Get Cloud Run status (ready condition, current revision)
2. Get last 30 log lines
3. Check for ERROR or CRITICAL log entries
4. Test live endpoint: GET https://adreel.studio/api/settings
5. Write a health summary: 🟢/🟡/🔴 with details
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def diagnose_deployment_failure() -> str:
    """Diagnose why a deployment might have failed."""
    task = """Diagnose potential deployment issues.

1. Check Cloud Run status — is the service Ready?
2. Get logs, focusing on startup errors
3. Check cloudbuild.yaml for configuration issues (read it)
4. Look for:
   - Missing env vars (ImportError, KeyError)
   - Port binding issues
   - OOM kills (Exit code 137)
   - Startup timeout
5. Write a diagnosis with recommended fix
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def trigger_deploy(reason: str = "manual deploy") -> str:
    """Trigger a Cloud Build deployment."""
    task = f"""Deploy the current code to Cloud Run.

Reason: {reason}

1. First check Cloud Run status to confirm current state
2. Read cloudbuild.yaml to confirm it looks correct
3. Trigger the deployment
4. Report the deployment output
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def check_env_vars() -> str:
    """Check what environment variables are configured on Cloud Run."""
    task = """Check the Cloud Run environment variable configuration.

Run: gcloud run services describe ads-video-hero --region us-central1 --format json
Parse the spec.template.spec.containers[0].env array.

List all configured env vars (mask secret values — show only first 4 chars).
Identify any that look missing or misconfigured.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def set_env_var(key: str, value: str) -> str:
    """Set a single environment variable on Cloud Run safely."""
    task = f"""Set the environment variable {key} on the Cloud Run service.

Use: gcloud run services update ads-video-hero --region us-central1 --update-env-vars {key}=<value>

IMPORTANT: Use --update-env-vars (not --set-env-vars) to preserve other vars.

After setting, verify it's visible in the service description.
"""
    # We don't pass value through the agent prompt for security; pass it as a separate instruction
    full_task = task + f"\n\nThe value to set is: {value}"
    return run_agent(SYSTEM, full_task, ALLOWED_TOOLS)
