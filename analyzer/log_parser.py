"""
log_parser.py

Why this file exists:
A raw CI log can be thousands of lines: dependency installs, cache
restores, successful steps. The LLM has a limited context window and
costs time/tokens per character — so we should never hand it the
whole raw log. This module's job is to cut a 2,000-line log down to
the 20-50 lines that actually matter, BEFORE it reaches the AI.

This is a classic "garbage in, garbage out" problem. A good filter
here makes the AI's explanation more accurate and faster, because it
isn't distracted by irrelevant noise.

Approach: keyword + pattern matching, not another AI call. We keep
this step simple and deterministic (regex/keywords) on purpose — it's
fast, free, and predictable. Save the AI budget for the part that
actually needs reasoning: explaining the error in plain English.
"""

import re

# Lines containing any of these (case-insensitive) are almost always
# worth keeping. This list is intentionally generic across languages
# (Node, Python, Docker, generic shell) since a pipeline can fail at
# many different steps.
ERROR_SIGNAL_KEYWORDS = [
    "error",
    "exception",
    "fail",
    "failed",
    "failure",
    "traceback",
    "fatal",
    "cannot find module",
    "command not found",
    "permission denied",
    "no such file or directory",
    "exit code 1",
    "exit code 127",
    "npm err",
    "syntaxerror",
    "typeerror",
    "referenceerror",
]

# Lines matching these patterns are noise we almost always want to
# drop, even if they happen to contain a keyword above (e.g. a log
# line literally named "error-handling-middleware.js" during a normal
# "installing dependencies" step).
NOISE_PATTERNS = [
    r"^added \d+ packages",
    r"^npm warn deprecated",
    r"^Downloading",
    r"^Receiving objects",
    r"^Resolving deltas",
]


def extract_error_lines(raw_log: str, context_lines: int = 2) -> str:
    """
    Scans the raw log line by line. Whenever a line matches an error
    signal, we keep it PLUS a few lines of surrounding context (default
    2 above and 2 below), because a bare error message on its own line
    ("Error: Cannot find module 'lodash'") is often meaningless without
    the line above it that says which file was being run.

    Returns a single trimmed string ready to hand to the AI.
    """
    lines = raw_log.splitlines()
    keep_indices = set()

    for i, line in enumerate(lines):
        lower = line.lower()

        if any(re.search(pattern, line) for pattern in NOISE_PATTERNS):
            continue

        if any(keyword in lower for keyword in ERROR_SIGNAL_KEYWORDS):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            keep_indices.update(range(start, end))

    if not keep_indices:
        # Fallback: if nothing matched our keywords, the failure might
        # use vocabulary we didn't anticipate. Rather than send nothing,
        # send the last N lines — pipeline failures very often surface
        # their real cause near the end of the log.
        tail = lines[-40:]
        return "\n".join(tail).strip()

    ordered_indices = sorted(keep_indices)
    relevant_lines = [lines[i] for i in ordered_indices]
    return "\n".join(relevant_lines).strip()


def extract_from_all_logs(logs_by_job: dict[str, str]) -> dict[str, str]:
    """Applies extract_error_lines() to every failed job's log."""
    return {job_name: extract_error_lines(log) for job_name, log in logs_by_job.items()}
