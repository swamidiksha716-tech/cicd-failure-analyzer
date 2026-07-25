"""
slack_notifier.py

Why this file exists:
The whole point of this project is getting the answer to a human
FAST, without them opening GitHub at all. Slack is where most dev
teams already live, so we push the AI's explanation there via an
Incoming Webhook — a simple URL that accepts a JSON payload and posts
it as a message. No Slack app, no OAuth, no bot token needed — that's
why it's the right tool for this project's scope.
"""

import requests


def format_message(repo: str, run_id: str, analyses_by_job: dict[str, str]) -> dict:
    """
    Builds the Slack payload using "blocks" (Slack's structured message
    format) instead of a single plain-text string, so the message is
    readable — headers, dividers, and a link back to the actual run.
    """
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 CI/CD Pipeline Failure"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Repo:* {repo}\n*Run:* <{run_url}|#{run_id}>",
            },
        },
    ]

    for job_name, analysis in analyses_by_job.items():
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Job:* `{job_name}`\n```{analysis}```"},
            }
        )

    return {"blocks": blocks}


def send_slack_notification(webhook_url: str, repo: str, run_id: str, analyses_by_job: dict[str, str]) -> None:
    payload = format_message(repo, run_id, analyses_by_job)
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
