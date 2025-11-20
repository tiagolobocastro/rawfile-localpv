# Install Guide

## Install

### Via Helm

```shell
helm repo add rawfile-localpv https://openebs.github.io/rawfile-localpv
helm repo update rawfile-localpv
helm install rawfile-localpv rawfile-localpv/rawfile-localpv -n openebs --create-namespace
```

> [!TIP]
We suggest you familiarize yourself with the [Charts' README.md](../deploy/helm/rawfile-localpv/README.md) and the [Charts' values.yaml](../deploy/helm/rawfile-localpv/values.yaml), as you may want to tune it to your liking

## Usage

You can create one or more storage classes using chart, by default we have a storage class named `rawfile-localpv`, but you can change the name or other options by changing chart values

## Upgrade

Before upgrading please read through the [Changelog](../CHANGELOG.md) as well as this document and follow any suggested recommendations to ensure a smooth upgrade

> [!WARNING]
Don't blind upgrade to a potentially breaking version as additional steps may be required

We try to do our best to follow [semantic versioning](https://semver.org/), but mistakes can happen. If you encounter any unexpected breaking change from our part, please do let us know!

### Upgrading to v0.12.0

This version introduces the following breaking changes:

- Btrfs snapshots has been deprecated
  New snapshots cannot be taken but we still allow deleting existing ones.
- Separate Data and Metadata dir
  The metadata defaults to $DATA/meta and the data is copied automatically by the node plugin

### Upgrading to v0.11.0

This version introduces the following breaking changes:

- Volumes are thick provisioned by default  \
  To retain existing thin behaviour you may set `thinProvision` storage class parameter to `false`
- Manifest install file has been removed
  Please use the helm chart package going forward. You may also generate equivalent file with `helm template`
- Analytics have been added and enabled default
  We'd appreciate it if you kept them enabled, but of course you may disable them through the helm var `.globals.analytics.enabled`

## Uninstall

Before uninstalling `rawfile-localpv` please make sure all resources created through `rawfile-localpv` are deleted:

1. Volume Snapshots
2. Persistent Volume Claims
3. Persistent Volumes

This will ensure there's no leaked mounts or linux loop devices in your system.

After you've done so, you should uninstall using the same method which you had used for install.

### Installed using Helm

```shell
helm uninstall rawfile-localpv -n openebs
```

### Installed using manifest (removed)

```shell
kubectl delete -f https://github.com/openebs/rawfile-localpv/raw/refs/heads/develop/deploy/rawfile-localpv-driver.yaml
```

[!WARNING]
Be sure to use the exact same yaml file which you had used to install

---

After uninstalling you may want to delete the `rawfile-localpv` data directory from each node.
