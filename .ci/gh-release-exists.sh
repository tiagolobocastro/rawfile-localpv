#/usr/bin/env bash

set -uo pipefail

VERSION="$1"
REPO=${2:-}

if [ "${REPO:-}" != "" ]; then
	REPO="--repo $REPO"
fi
SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/common"

command -v gh &>/dev/null || die 'GitHub gh client is not installed. Aborting.'

STDOUT=$(gh release view "v${VERSION#v}" $REPO 2>&1)
error=$?
if [ "$STDOUT" = "release not found" ]; then
	if [ $error -eq 1 ]; then
		echo -n "not-found"
		exit 0
	fi
elif [ $error -eq 0 ]; then
	echo -n "found"
	exit 0
fi

echo "error: $STDOUT" >&1
exit 1
