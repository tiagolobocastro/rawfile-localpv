#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]:-"$0"}")")"
source "$SCRIPT_DIR/common"
ROOT_DIR="$SCRIPT_DIR/.."
CHART_DIR="$ROOT_DIR/deploy/helm/rawfile-localpv"

command -v helm >/dev/null 2>&1 || die "Helm is not installed. Aborting."
helm template "$CHART_DIR" --debug
helm lint "$CHART_DIR"
