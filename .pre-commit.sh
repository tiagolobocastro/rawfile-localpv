#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(dirname "$0")"
CHART_DIR="$ROOT_DIR/deploy/helm/rawfile-localpv"
CHART="$CHART_DIR/Chart.yaml"

help() {
	cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -h, --help                        Display this text.
  --version-sync                    Sync the pyproject version with the chart version and appVersion.

Examples:
  $(basename "$0") --version-sync
EOF
}

DONE=
while [ "$#" -gt 0 ]; do
	case $1 in
	-h | --help)
		break
		shift
		;;
	--version-sync)
		PY_VERSION=$(grep -Pom1 '(?<=version = ")[^"]*' "$ROOT_DIR/pyproject.toml")
		sed -i'' -e "s/^version: .*/version: $PY_VERSION/" "$CHART"
		sed -i'' -e "s/^appVersion: .*/appVersion: $PY_VERSION/" "$CHART"
		DONE="yes"
		shift
		;;
	*)
		echo -e "Unknown parameter $1" >&2
		help
		exit 1
		;;
	esac
done

if [ -z "${DONE:-}" ]; then
	help
	exit 0
fi
