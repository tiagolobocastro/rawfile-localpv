#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$0")"
ROOT_DIR="$SCRIPT_DIR"/..

set -euo pipefail

cd "$ROOT_DIR/rawfile/tests"
pytest test_smoke.py --junit-xml="./report.xml" --durations=20
