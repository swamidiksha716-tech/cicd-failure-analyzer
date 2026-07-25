"""
report_generator.py

Why this file exists:
A Slack message disappears into scroll-back within a day. If you want
to answer "how many times has this exact error happened this month?"
or show a portfolio reviewer a concrete artifact, you need a durable,
structured record. JSON is the right format here — it's easy to parse
later (e.g. to build a dashboard) and it's the same format GitHub's
own API already speaks, so there's no format-translation cost.
"""

import json
import os
from datetime import datetime, timezone


def generate_report(repo: str, run_id: str, analyses_by_job: dict[str, str], reports_dir: str) -> str:
    """
    Builds one JSON file per failed run. Returns the path it was
    written to.

    We timestamp + include the run_id in the filename so reports never
    collide and sort chronologically in a file browser.
    """
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{timestamp}_run-{run_id}.json"
    filepath = os.path.join(reports_dir, filename)

    report = {
        "repository": repo,
        "run_id": run_id,
        "generated_at": timestamp,
        "run_url": f"https://github.com/{repo}/actions/runs/{run_id}",
        "failures": [
            {"job_name": job_name, "analysis": analysis}
            for job_name, analysis in analyses_by_job.items()
        ],
    }

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    return filepath
