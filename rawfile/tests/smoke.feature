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
    # | Immediate            | ReadWriteOnce | null    | Block       | null          |
    | WaitForFirstConsumer | ReadWriteOnce | ext4    | Filesystem  | null          |
    # | WaitForFirstConsumer | ReadWriteOnce | null    | Block       | null          |

  Scenario: Butter FS Snapshots and Restores
    Given a Persistent Volume Claim with Filesystem btrfs
    Then we create a pod which mounts the PVC
    And we write some data to the mount path
    When we create a snapshot referencing the PVC
    Then the snapshot is eventually ready
    #And we write some more data to the mount path
    # todo: restores not working yet
    #When we create a restore volume from the snapshot
    #And we create a pod which mounts the restore PVC
    #Then the restored volume should contain the snapshot data

  Scenario: Deleting Snapshot of unstaged volume
    Given a Persistent Volume Claim with Filesystem btrfs
    Then we create a pod which mounts the PVC
    And we write some data to the mount path
    And we terminate the btrfs app pod
    And the volume is unstaged
    When we create a snapshot referencing the PVC
    Then the snapshot is eventually ready
    When we delete the snapshot
    Then it should be eventually be deleted
