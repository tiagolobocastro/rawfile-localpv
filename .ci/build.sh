#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$0")"
DREG=${DREG:-"docker.io"}
CI_REGISTRY="$DREG"

set -exuo pipefail
source "$SCRIPT_DIR/common"

command -v docker &>/dev/null || ( echo 'Docker is not installed. Aborting.'; exit 1 )
docker buildx version &>/dev/null || ( echo 'Docker Buildx plugin is not installed. Aborting.'; exit 1 )

export PUSH_OPTION=""
export IMAGE_TAGS="${CI_TEST_IMAGE_TAG}"
export NO_CACHE_OPTIONS=""

if [ "${CI_IMAGE_PLATFORMS}" = "local" ]; then
  export IMAGE_DESTINATION="docker"
else
  export IMAGE_DESTINATION="registry"
  if [ -n "${DNAME:-}" ] && [ -n "${DPASS:-}" ]; then
    docker login -u "${DNAME}" -p "${DPASS}" "$CI_REGISTRY"
    export PUSH_OPTION="--push"
  fi
  export IMAGE_TAGS="${COMMIT} ${BRANCH_SLUG} ${IMAGE_TAG}";
  export NO_CACHE_OPTIONS="--pull --no-cache"
fi

for t in ${IMAGE_TAGS}; do
  TAGS_ARGS+=" -t $(build-image-uri ${t})"
done

if [ -n "${IMAGE_TAG:-}" ] && [ "$IMAGE_DESTINATION" = "registry" ]; then
  COMMIT=$IMAGE_TAG
fi

docker buildx build \
  ${TAGS_ARGS} \
  ${PUSH_OPTION} \
  ${NO_CACHE_OPTIONS} \
  --output=type=${IMAGE_DESTINATION} \
  --platform="${CI_IMAGE_PLATFORMS}" \
  --build-arg "IMAGE_REPOSITORY=${IMAGE}" \
  --build-arg "IMAGE_TAG=${COMMIT}" \
  "$SCRIPT_DIR/.."

if [ "$(kubectl config current-context)" = "kind-rawfile" ]; then
  kind load docker-image $(build-image-uri ${CI_TEST_IMAGE_TAG}) --name "rawfile"
fi
