# 📄 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - YYYY-MM-DD ⚠️ Breaking Changes

### Added ✨

- A new logging system for easier tracing/support
- Serialization of CSI volume operations
- New storage class parameter: `formatOptions` to specify filesystem creation/formatting options
- New storage class parameter: `thinProvision` to control full storage allocation or on-demand
- Support for reserved storage/capacity override support on nodes via helm variable configuration: `reservedCapacity` and `capacityOverride`

### Fixed 🐛

- Add missing helm components for btrfs snapshots on K8s
- Delete snapshot if source data has already been deleted
- Atomically update metadata and file image
- Use `mountOptions` from the storage class when mounting a filesystem

### Changed ♻️

- Refactored FS Support and Utilities to be more standard
- ⚠️ Thick volumes are now the default ⚠️  \
  To retain existing thin behaviour you may set `thinProvision` storage class parameter to `true`
- Switched to the official K8s client library

### Internal 🔧

- Increase kubelet sync frequency for testing
- Add and use [Mergify](https://mergify.com/) bot for `GitHub Actions`
- Improved `nixos-shell` experience for dev
- Add helm-docs pre-commit hook
- Added Contributor documentation

### Known Issues 🚫

- ReadOnly attribute in PVC template not fully handled
- Volume restore/clone not implemented

---

## [v0.10.0] - 2025-06-18

> [GitHub Release](https://github.com/openebs/rawfile-localpv/releases/tag/v0.10.0)

### Added ✨

- Direct I/O for near-zero disk performance overhead
- Support for `Block` volume mode
- Helm chart package publishing
- Add `fsType` to storageClass in helm
- Signal handling for graceful pod termination in K8s

### Fixed 🐛

- Volume expansion issues
- Parent folder creation and idempotency on volume publishing
- Race condition during volume deletion (img file leak)
- Loop device cleanup and idempotency
- Skip node expand if the volume is not staged

### Security 🛡️

- Restrict permissions on existing data/image path  \
  Update existing ones on migration

### Changed ♻️

- Updated CSI spec to v1.10.0
- Refactored deployment manifests
- Improved logging and error handling
- ⚠️ Large Helm Chart overhaul ⚠️

### Internal 🔧

- Refactored deployment manifests
- Improved README.md documentation
- Migrated CI from `Travis` to `GitHub Actions`
- Implemented stale action to manage old PRs/issues
- Added smoke tests for reliable builds
- Upgraded Python environment (now using Poetry for dependency management)
- Multiple dependency bumps across the stack, ensuring security and stability
- Added Dependabot for automated dependency updates
- Introduced a CODEOWNERS file to streamline code ownership
- Local testing with kind or vm through nixos-shell
- Add pre-commit and format the code
- Fix OpenSSF link and Add pre-commit.ci badge
- Skip tests on docs only changes

### Known Issues 🚫

- ReadOnly attribute in PVC template not fully handled
- Volume restore/clone not implemented
