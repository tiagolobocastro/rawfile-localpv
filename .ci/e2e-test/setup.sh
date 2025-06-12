#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$0")"

set -ex
source "$SCRIPT_DIR/../common"

TAG="${CI_TEST_IMAGE_TAG}"
if [ -n "${CI_RELEASE_TAG:-}" ]; then
  TAG="$CI_RELEASE_TAG"
  TAG_SUFFIX=
fi
URI="$(build-image-uri ${TAG})"
TAG="$(build-image-tag ${TAG})"

echo "Image URI: $URI"
echo "Image Tag: $TAG"

if [ -n "${CI_RELEASE_TAG:-}" ]; then
  docker pull "$URI"
fi

if [ "$(kubectl config current-context)" = "kind-rawfile" ]; then
  kind load docker-image "$URI" --name "rawfile"
fi

CHART="$SCRIPT_DIR/../../deploy/helm/rawfile-csi/"
if [ -n "${CI_CHART:-}" ]; then
  helm repo add rawfile-csi "$CI_CHART"
  CHART="rawfile-csi/rawfile-csi --version ${TAG#v}"
fi

helm upgrade --wait \
  -n openebs --create-namespace -i rawfile-csi \
  --set metrics.serviceMonitor.enabled=false \
  --set image.registry=$CI_REGISTRY,image.repository=$CI_IMAGE_REPO,image.tag=$TAG,image.pullPolicy=Never \
  $CHART

kubectl wait --for=condition=ready pod --all -n openebs
kubectl get pods -n openebs -o wide
