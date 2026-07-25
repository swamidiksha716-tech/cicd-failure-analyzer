"""
main.py

Why this file exists:
This is the entry point — the "conductor" that calls each module in
the correct order and handles top-level errors/logging. Nothing in
this file does real work itself; it just wires together:

    log_collector -> log_parser -> ai_analyzer -> slack_notifier
                                                 -> report_generator

This is intentional. Keeping orchestration separate from logic means
each module (collector, parser, analyzer, notifier, reporter) can be
unit-tested on its own, without needing a real GitHub Actions run or a
real Slack webhook.

Run this script FROM inside a GitHub Actions workflow, after a job has
failed (see .github/workflows/deploy.yml, the `on-failure` job).
"""

import logging
import sys

from config import load_config
from log_collector import collect_failure_logs
from log_parser import extract_from_all_logs
from ai_analyzer import analyze_all_failures
from slack_notifier import send_slack_notification
from report_generator import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("cicd-failure-analyzer")


def main() -> int:
    try:
        config = load_config()
    except EnvironmentError as e:
        logger.error(str(e))
        return 1

    logger.info(f"Collecting logs for failed jobs in run {config.github_run_id}...")
    raw_logs = collect_failure_logs(config.github_repo, config.github_run_id, config.github_token)

    if not raw_logs:
        logger.info("No failed jobs found for this run. Nothing to analyze.")
        return 0

    logger.info(f"Found {len(raw_logs)} failed job(s): {list(raw_logs.keys())}")

    logger.info("Extracting relevant error lines...")
    error_excerpts = extract_from_all_logs(raw_logs)

    logger.info(f"Sending error excerpts to {config.ollama_model} via Ollama for analysis...")
    analyses = analyze_all_failures(error_excerpts, config.ollama_host, config.ollama_model)

    logger.info("Posting analysis to Slack...")
    send_slack_notification(config.slack_webhook_url, config.github_repo, config.github_run_id, analyses)

    logger.info("Saving deployment failure report...")
    report_path = generate_report(config.github_repo, config.github_run_id, analyses, config.reports_dir)
    logger.info(f"Report saved to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
