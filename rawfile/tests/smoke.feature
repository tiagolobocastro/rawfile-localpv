Feature: Basic Functionality

  Background:
    Given a Kubernetes cluster with rawfile-localpv installed

  Scenario Outline: Create PVCs with different storage parameters
    When I create a Persistent Volume Claim with <binding_mode> <access_mode> <fs_type> <volume_mode> <mount_options>
    Then the PVC should be bound if Binding mode is Immediate
    When a pod is created with the above PVC
    Then the PVC should be bound
    And the pod should complete with success
    When the PVC is expanded
    Then the Block PVCs status reflect the expanded size
    And the Filesystem PVC is pending node expansion
    When another pod is created with the above PVC
    Then the PVC status reflects the expanded size
    And the POD sees the expanded size

  Examples:
    | binding_mode         | access_mode   | fs_type | volume_mode | mount_options |
    | Immediate            | ReadWriteOnce | ext4    | Filesystem  | noatime       |
    | Immediate            | ReadWriteOnce | xfs     | Filesystem  | inode64       |
    | Immediate            | ReadWriteOnce | btrfs   | Filesystem  | null          |
    | Immediate            | ReadWriteOnce | null    | Block       | null          |
    | WaitForFirstConsumer | ReadWriteOnce | ext4    | Filesystem  | null          |
    | WaitForFirstConsumer | ReadWriteOnce | null    | Block       | null          |

  Scenario Outline: Snapshot creates and restores with different parameters and successfully remove it
    When I create a Persistent Volume Claim with <copy_on_write> <fsfreeze> for snapshotting
    Then we create a pod which mounts the PVC
    And we write some data to the mount path
    And delete pod if snapshotting of inused volume is disabled
    When we create a snapshot referencing the PVC
    Then the snapshot is eventually ready
    When we create a restore volume from the snapshot
    And we create a pod which mounts the restore PVC
    Then the restored volume should contain the snapshot data
    When we delete the snapshot
    Then it should be eventually be deleted

  Examples:
    | copy_on_write | fsfreeze |
    | false         | false    |
    | true          | false    |
    | false         | true     |
