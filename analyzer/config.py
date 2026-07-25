"""
config.py

Why this file exists:
Every script in this project needs a handful of secrets/settings
(GitHub token, repo name, Slack webhook URL, Ollama endpoint). Instead
of each file reading environment variables directly (which makes it
easy to typo a variable name in five different places), we read them
ALL in one place and expose them as a single object. If a setting is
missing, we fail fast with a clear error instead of a confusing crash
three files later.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    github_token: str
    github_repo: str          # format: "owner/repo"
    github_run_id: str        # the specific failed workflow run to analyze
    slack_webhook_url: str
    ollama_host: str
    ollama_model: str
    reports_dir: str


def load_config() -> Config:
    """
    Reads required settings from environment variables.

    In GitHub Actions, these are injected via `env:` in the workflow
    YAML (secrets.GITHUB_TOKEN, secrets.SLACK_WEBHOOK_URL, etc).
    Locally, you'd put them in a `.env` file (see .env.example) and
    load it with a tool like python-dotenv before running main.py.
    """
    required = {
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
        "GITHUB_REPOSITORY": os.environ.get("GITHUB_REPOSITORY"),
        "GITHUB_RUN_ID": os.environ.get("GITHUB_RUN_ID"),
        "SLACK_WEBHOOK_URL": os.environ.get("SLACK_WEBHOOK_URL"),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in your GitHub Actions workflow `env:` block or in a local .env file."
        )

    return Config(
        github_token=required["GITHUB_TOKEN"],
        github_repo=required["GITHUB_REPOSITORY"],
        github_run_id=required["GITHUB_RUN_ID"],
        slack_webhook_url=required["SLACK_WEBHOOK_URL"],
        ollama_host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3.2"),
        reports_dir=os.environ.get("REPORTS_DIR", "reports"),
    )
