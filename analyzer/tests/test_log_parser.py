"""
test_log_parser.py

Why we're testing THIS module first:
log_collector needs a real GitHub token + API, ai_analyzer needs a
real running Ollama instance, slack_notifier needs a real webhook.
log_parser is pure logic (string in, string out) with no external
dependencies — so it's the cheapest, fastest module to test, and the
best place to build the habit of testing as we go.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from log_parser import extract_error_lines


SAMPLE_LOG = """
Run npm install
added 842 packages in 12s
npm warn deprecated request@2.88.2: request has been deprecated
Run npm test
> jest --ci

FAIL tests/server.test.js
  ● GET /nonexistent should not exist, but we assert it does

    TypeError: Cannot read properties of undefined (reading 'statusCode')

      at Object.<anonymous> (tests/server.test.js:24:9)

Tests:       1 failed, 2 passed, 3 total
npm ERR! Test failed. See above for more details.
Error: Process completed with exit code 1.
"""


def test_extracts_error_lines_and_drops_noise():
    result = extract_error_lines(SAMPLE_LOG)

    assert "TypeError" in result
    assert "npm ERR!" in result
    assert "exit code 1" in result
    # noise lines should be filtered out
    assert "added 842 packages" not in result
    assert "npm warn deprecated" not in result


def test_falls_back_to_tail_when_no_keywords_match():
    boring_log = "\n".join(f"step {i} completed" for i in range(100))
    result = extract_error_lines(boring_log)

    # should still return something (the tail), not an empty string
    assert result != ""
    assert "step 99 completed" in result


if __name__ == "__main__":
    test_extracts_error_lines_and_drops_noise()
    test_falls_back_to_tail_when_no_keywords_match()
    print("All log_parser tests passed.")
