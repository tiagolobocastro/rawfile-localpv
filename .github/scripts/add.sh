#!/usr/bin/env bash
# add-branch-to-ruleset.sh
#
# Resolves the ruleset by name, then appends the new release branch
# to its ref include list.
#
# Required env vars (set by the workflow):
#   GH_TOKEN       - PAT or GitHub App token with Administration: write
#   RULESET_NAME   - Name of the merge queue ruleset (e.g. "MergeQueue")
#   BRANCH_NAME    - The newly created branch (e.g. release/1.4.0)
#                    NOTE: github.event.ref is the bare branch name, no refs/heads/ prefix
#   REPO           - owner/repo (e.g. acme/my-service)

set -euo pipefail

# github.event.ref is already a bare branch name (e.g. release/1.4.0),
# so we add the refs/heads/ prefix here — just once
REF_PATTERN="refs/heads/${BRANCH_NAME}"

echo "Resolving ruleset ID for '${RULESET_NAME}' ..."
RULESET_ID=$(
  gh api "/repos/${REPO}/rulesets" \
    | jq -r --arg name "${RULESET_NAME}" '.[] | select(.name == $name) | .id'
)

if [[ -z "${RULESET_ID}" ]]; then
  echo "::error::No ruleset found with name '${RULESET_NAME}'"
  exit 1
fi

echo "Resolved '${RULESET_NAME}' → ID ${RULESET_ID}"

RULESET_PATH="/repos/${REPO}/rulesets/${RULESET_ID}"

echo "Fetching ruleset ..."
ruleset=$(gh api "${RULESET_PATH}")

# Extract current include and exclude lists (default to empty JSON arrays if absent)
include_list=$(echo "${ruleset}" | jq '.conditions.ref_name.include // []')
exclude_list=$(echo "${ruleset}" | jq '.conditions.ref_name.exclude // []')

# Idempotency check — don't add duplicates
if echo "${include_list}" | jq -e --arg ref "${REF_PATTERN}" '. | index($ref) != null' > /dev/null; then
  echo "Branch ${REF_PATTERN} is already in the ruleset. Nothing to do."
  exit 0
fi

# Append the new branch to the include list
updated_include=$(echo "${include_list}" | jq --arg ref "${REF_PATTERN}" '. + [$ref]')

echo "Adding ${REF_PATTERN} to ruleset. New include list:"
echo "${updated_include}" | jq .

# Use --input with a full JSON body to avoid any field encoding issues
patch_body=$(jq -cn \
  --argjson include "${updated_include}" \
  --argjson exclude "${exclude_list}" \
  '{conditions: {ref_name: {include: $include, exclude: $exclude}}}')

echo "${patch_body}" | gh api "${RULESET_PATH}" \
  --method PATCH \
  --input -

echo "✅ Ruleset '${RULESET_NAME}' (${RULESET_ID}) updated successfully."
