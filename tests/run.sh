#!/usr/bin/env bash
# Run every test of the core. Each test prints PASS or FAIL lines; the exit code is non-zero if one fails.
cd "$(dirname "$0")/.."
status=0
for t in tests/test_*.py; do python3 "$t" || status=1; done
for t in tests/test_*.sh; do bash "$t" || status=1; done
exit $status
