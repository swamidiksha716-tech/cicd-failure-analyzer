"""
ai_analyzer.py

Why this file exists:
This is the "intelligence" layer. It takes the short, filtered error
text from log_parser.py and asks a local LLM (Llama 3.2, served by
Ollama) to explain it and suggest a fix.

Why Ollama + Llama 3.2 instead of a paid API (OpenAI, Anthropic API)?
  - Cost: this is a portfolio/demo project — a local model is free to
    run as many times as we want while testing.
  - Privacy: logs can contain internal file paths, env var names, even
    partial secrets. Keeping analysis local means nothing leaves your
    machine/runner.
  - Trade-off: Llama 3.2 (especially smaller variants) is less capable
    than a large hosted model, and running it inside a GitHub Actions
    runner means installing Ollama + pulling the model on every run,
    which is slow. In a real production setup you'd likely swap this
    for a hosted API and cache/rate-limit calls — but the KEY POINT
    for an interview is that this module is swappable: nothing outside
    this file needs to know which LLM backend is being used.
"""

import requests


def build_prompt(job_name: str, error_text: str) -> str:
    """
    Prompt engineering matters here. We explicitly tell the model:
    - its role (senior DevOps engineer)
    - the exact output format we want (so it's easy to parse and post
      to Slack consistently, instead of getting a different essay
      structure every run)
    - to stay grounded in the provided log text, not invent details
    """
    return f"""You are a senior DevOps engineer reviewing a failed CI/CD job.

Job name: {job_name}

Relevant log excerpt:
---
{error_text}
---

Respond in exactly this format:

SUMMARY: <one sentence, plain English, what broke>
LIKELY CAUSE: <2-3 sentences on why this most likely happened>
SUGGESTED FIX: <concrete, actionable steps to fix it>

Only use information present in the log excerpt above. If the log is unclear, say so instead of guessing.
"""


def analyze_with_ollama(job_name: str, error_text: str, host: str, model: str) -> str:
    """
    Calls the local Ollama server's /api/generate endpoint.

    Ollama must already be running (`ollama serve`) with the model
    pulled (`ollama pull llama3.2`) before this call will succeed.
    """
    prompt = build_prompt(job_name, error_text)

    response = requests.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,  # simpler to handle: one full response, not a token stream
        },
        timeout=120,  # local LLM inference can be slow, especially on CPU-only runners
    )
    response.raise_for_status()

    return response.json().get("response", "").strip()


def analyze_all_failures(errors_by_job: dict[str, str], host: str, model: str) -> dict[str, str]:
    """Runs analyze_with_ollama() for every failed job's extracted error text."""
    return {
        job_name: analyze_with_ollama(job_name, error_text, host, model)
        for job_name, error_text in errors_by_job.items()
    }
