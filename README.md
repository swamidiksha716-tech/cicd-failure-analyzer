# Intelligent CI/CD Failure Analyzer

Automatically detects CI/CD pipeline failures, pulls the logs, extracts the
relevant error lines, explains the failure in plain English using a local
LLM (Llama 3.2 via Ollama), suggests a fix, posts it to Slack, and saves a
structured JSON report — so a developer never has to manually scroll a
2,000-line log to find out what broke.

## The problem this solves

When a deployment fails, GitHub Actions gives you a raw, often huge log.
Finding the actual error inside it costs a developer real time on every
failure. This project automates that first triage step: it reads the log
*for* you and hands back a short, plain-English "here's what broke and how
to fix it."

## Architecture

```
 Developer pushes code
         |
         v
      GitHub
         |
         v
  GitHub Actions (build -> test -> deploy)
         |
         | (if any step fails)
         v
  analyze-failure job triggers
         |
         v
  log_collector.py  ---- calls GitHub REST API, downloads raw logs
         |
         v
  log_parser.py     ---- strips noise, keeps only error-relevant lines
         |
         v
  ai_analyzer.py    ---- sends error excerpt to Llama 3.2 (via Ollama)
         |                gets back: summary, likely cause, suggested fix
         v
  slack_notifier.py ---- posts formatted analysis to a Slack channel
         |
         v
  report_generator.py -- saves a timestamped JSON report to /reports
```

Each box is a separate Python module with exactly one job. That's
deliberate — it's the "single responsibility principle," and it means you
can test, replace, or explain any one piece without touching the others
(e.g., swap Llama for a hosted API later by only editing `ai_analyzer.py`).

## Project structure

```
cicd-failure-analyzer/
├── sample-app/              # the Node.js app the pipeline builds & deploys
│   ├── server.js
│   ├── package.json
│   └── tests/server.test.js
├── .github/workflows/
│   └── deploy.yml           # the actual CI/CD pipeline definition
├── analyzer/                 # the Python failure-analysis toolkit
│   ├── config.py             # loads/validates all env vars in one place
│   ├── log_collector.py      # pulls raw logs from GitHub Actions API
│   ├── log_parser.py         # filters raw logs down to error-relevant lines
│   ├── ai_analyzer.py        # sends filtered text to Llama 3.2 via Ollama
│   ├── slack_notifier.py     # posts the analysis to Slack
│   ├── report_generator.py   # saves a JSON report per failed run
│   ├── main.py                # orchestrates all of the above, in order
│   ├── requirements.txt
│   ├── reports/               # generated JSON reports land here
│   └── tests/test_log_parser.py
├── .env.example
└── .gitignore
```

## Why each technology was chosen

| Tech | Why | Alternative considered | Trade-off |
|---|---|---|---|
| **GitHub Actions** | Free, tightly integrated with GitHub, YAML-based, industry standard | Jenkins, CircleCI | Jenkins is more configurable but needs a server to host/maintain — overkill for this project |
| **Python (analyzer)** | Excellent for scripting + HTTP calls + JSON handling, huge ecosystem | Node.js for everything | Using Python here (vs. Node) also shows you can work across a polyglot stack, which is realistic for a DevOps role |
| **Node.js (sample app)** | Simple, fast to demo, most common language for a "sample app" a pipeline builds | Python Flask app | Keeps the pipeline realistic — most companies deploy Node/frontend apps this way |
| **Ollama + Llama 3.2** | Free, runs locally, no per-request API cost, keeps log contents private | OpenAI/Anthropic API | Hosted APIs are more capable and faster but cost money per call and send your logs to a third party — a real trade-off worth explaining in an interview |
| **Slack Incoming Webhook** | Simplest way to post messages — just a URL + JSON POST, no OAuth/bot setup | Slack Bot API, email | A full bot could also *respond* to messages, but a webhook is the right amount of complexity for one-way notifications |
| **JSON reports** | Human-readable, easy to parse programmatically later (e.g. for a dashboard) | Database (e.g. SQLite) | A database would scale better long-term, but flat JSON files are simpler to demo and version-control |
| **AWS Amplify** | Matches your existing AWS experience, simple hosting for a demo Node app | EC2 manually, Elastic Beanstalk | Amplify handles build/deploy config for you — less to explain for a "sample app," more room to focus on the analyzer itself |

## Setup

### 1. Prerequisites
- Node.js 20+, Python 3.11+, Git, a GitHub account
- [Ollama](https://ollama.com) installed locally (`ollama pull llama3.2`)
- A Slack workspace where you can create an [Incoming Webhook](https://api.slack.com/messaging/webhooks)

### 2. Local setup
```bash
git clone <your-repo-url>
cd cicd-failure-analyzer

# sample app
cd sample-app && npm install && npm test && cd ..

# analyzer
cd analyzer && pip install -r requirements.txt && cd ..

cp .env.example .env   # fill in your real values, never commit this file
```

### 3. GitHub repo setup
Push this to a new GitHub repo, then add these under
**Settings → Secrets and variables → Actions → New repository secret**:
- `SLACK_WEBHOOK_URL`
(`GITHUB_TOKEN` is provided automatically by GitHub Actions — you don't set it yourself.)

### 4. Triggering a demo failure
Open `sample-app/tests/server.test.js`, uncomment the block marked
`DEMO_FAILURE`, commit, and push. The test will genuinely fail, which
triggers the `analyze-failure` job — you'll see the whole pipeline run in
the **Actions** tab, and (if Slack is configured) a message land in your
channel a minute or two later. Comment it back out afterward.

## Testing

`analyzer/tests/test_log_parser.py` unit-tests the one fully local, no-external-service
module. Run it with:
```bash
cd analyzer && python tests/test_log_parser.py
```
The other modules (`log_collector`, `ai_analyzer`, `slack_notifier`) depend on
live external services (GitHub API, Ollama, Slack) — in a real team, these
would typically be tested with mocked HTTP responses (e.g. `unittest.mock` or
`responses`), which is a natural next improvement.

## Interview talking points

- **Why not send the whole log to the LLM?** Cost, latency, and context-window
  limits. Filtering first (log_parser.py) is a deliberate design choice —
  explain it as "garbage in, garbage out."
- **Why separate modules instead of one script?** Single responsibility —
  each piece can be tested, replaced, or debugged independently.
- **What would you change for production scale?** Swap Ollama for a hosted
  API with rate limiting, move JSON reports into a real database, add retry
  logic + dead-letter handling for the Slack call, and add caching so
  identical/recurring errors don't re-trigger a full LLM call every time.
- **What's the single biggest limitation right now?** Local LLM quality —
  Llama 3.2 is good but not as reliable as a large hosted model, and running
  Ollama inside a GitHub-hosted runner adds real time (installing + pulling
  the model) to every failed run.

## Possible next steps
- Cache/deduplicate repeated identical failures instead of re-analyzing every time
- Add a small dashboard (read the JSON reports) to show failure trends over time
- Add mocked unit tests for `log_collector`, `ai_analyzer`, and `slack_notifier`
