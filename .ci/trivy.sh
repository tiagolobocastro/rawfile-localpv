#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$0")"

set -exuo pipefail
source "$SCRIPT_DIR/common"

command -v trivy || die 'Trivy is not installed. Aborting.'
export CI_TEST=true
"$SCRIPT_DIR"/build.sh

export TRIVY_OUTPUT=./trivy-report.sarif
export TRIVY_FORMAT=sarif
export TRIVY_SEVERITY="HIGH,CRITICAL"
export TRIVY_PKG_TYPES="os,library"
export TRIVY_IGNORE_UNFIXED=false
export TRIVY_SCANNERS="vuln,secret,misconfig"

trivy image $(build-image-uri $CI_TEST_IMAGE_TAG)
