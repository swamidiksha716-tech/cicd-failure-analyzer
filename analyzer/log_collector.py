"""
log_collector.py

Why this file exists:
GitHub doesn't push logs to you when a job fails — you have to pull
them via the REST API. This module's ONE job is: given a repo and a
run ID, download the raw log text for whichever job(s) failed.

We separate this from parsing (log_parser.py) and analysis
(ai_analyzer.py) on purpose — each module does one thing. This is the
"single responsibility principle": if GitHub changes their API
tomorrow, only this file needs to change. If we swap Llama for a
different model later, only ai_analyzer.py changes.
"""

import requests


GITHUB_API_BASE = "https://api.github.com"


def get_failed_jobs(repo: str, run_id: str, token: str) -> list[dict]:
    """
    Step 1: Ask GitHub "which jobs in this run failed?"

    A single workflow run (e.g. "CI Pipeline #42") can contain multiple
    jobs (build, test, deploy). We only want logs from the ones that
    actually failed — pulling logs for successful jobs would just add
    noise for the AI to wade through later.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/runs/{run_id}/jobs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # crash loudly on 401/404 rather than silently returning nothing

    jobs = response.json().get("jobs", [])
    return [job for job in jobs if job.get("conclusion") == "failure"]


def download_job_log(repo: str, job_id: int, token: str) -> str:
    """
    Step 2: For one failed job, download its full raw log as plain text.

    GitHub returns this as a redirect to a signed URL, but the
    `requests` library follows redirects automatically by default, so
    we don't need to handle that ourselves.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/jobs/{job_id}/logs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def collect_failure_logs(repo: str, run_id: str, token: str) -> dict[str, str]:
    """
    Orchestrates the two steps above and returns a dict of
    { job_name: raw_log_text } for every job that failed.

    This is the function other files should actually call — they
    shouldn't need to know about the two-step GitHub API dance above.
    """
    failed_jobs = get_failed_jobs(repo, run_id, token)

    logs = {}
    for job in failed_jobs:
        job_name = job["name"]
        job_id = job["id"]
        logs[job_name] = download_job_log(repo, job_id, token)

    return logs
