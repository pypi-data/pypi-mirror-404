from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_backup_job_mode import EAgentBackupJobMode
from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_policy_storage_model import AgentBackupPolicyStorageModel
    from ..models.agent_object_model import AgentObjectModel
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.linux_agent_backup_job_files_model import LinuxAgentBackupJobFilesModel
    from ..models.linux_agent_backup_job_guest_processing_model import LinuxAgentBackupJobGuestProcessingModel
    from ..models.linux_agent_backup_job_volumes_model import LinuxAgentBackupJobVolumesModel


T = TypeVar("T", bound="LinuxAgentManagementBackupServerPolicySpec")


@_attrs_define
class LinuxAgentManagementBackupServerPolicySpec:
    """Backup policy settings for Veeam Agent for Linux. The settings apply to the `server` protected computer type.

    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        backup_mode (EAgentBackupJobMode): Backup job mode. Indicates the scope of the data you want to back up.
        storage (AgentBackupPolicyStorageModel): Backup policy storage settings
        computers (list[AgentObjectModel] | Unset): Array of protected computers.
        use_snapshotless_file_level_backup (bool | Unset): If `true`, the backup job will create a crash-consistent
            file-level backup without a snapshot. Available for the `FileLevel` backup mode only.
        volumes (LinuxAgentBackupJobVolumesModel | Unset): Details on volume objects.
        files (LinuxAgentBackupJobFilesModel | Unset): Backup scope settings for Veeam Agent for Linux backup jobs.
        guest_processing (LinuxAgentBackupJobGuestProcessingModel | Unset): Guest processing settings for Veeam Agent
            for Linux backup job.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    name: str
    type_: EJobType
    description: str
    backup_mode: EAgentBackupJobMode
    storage: AgentBackupPolicyStorageModel
    computers: list[AgentObjectModel] | Unset = UNSET
    use_snapshotless_file_level_backup: bool | Unset = UNSET
    volumes: LinuxAgentBackupJobVolumesModel | Unset = UNSET
    files: LinuxAgentBackupJobFilesModel | Unset = UNSET
    guest_processing: LinuxAgentBackupJobGuestProcessingModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        description = self.description

        backup_mode = self.backup_mode.value

        storage = self.storage.to_dict()

        computers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.computers, Unset):
            computers = []
            for computers_item_data in self.computers:
                computers_item = computers_item_data.to_dict()
                computers.append(computers_item)

        use_snapshotless_file_level_backup = self.use_snapshotless_file_level_backup

        volumes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.volumes, Unset):
            volumes = self.volumes.to_dict()

        files: dict[str, Any] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = self.files.to_dict()

        guest_processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_processing, Unset):
            guest_processing = self.guest_processing.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "description": description,
                "backupMode": backup_mode,
                "storage": storage,
            }
        )
        if computers is not UNSET:
            field_dict["computers"] = computers
        if use_snapshotless_file_level_backup is not UNSET:
            field_dict["useSnapshotlessFileLevelBackup"] = use_snapshotless_file_level_backup
        if volumes is not UNSET:
            field_dict["volumes"] = volumes
        if files is not UNSET:
            field_dict["files"] = files
        if guest_processing is not UNSET:
            field_dict["guestProcessing"] = guest_processing
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_policy_storage_model import AgentBackupPolicyStorageModel
        from ..models.agent_object_model import AgentObjectModel
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.linux_agent_backup_job_files_model import LinuxAgentBackupJobFilesModel
        from ..models.linux_agent_backup_job_guest_processing_model import LinuxAgentBackupJobGuestProcessingModel
        from ..models.linux_agent_backup_job_volumes_model import LinuxAgentBackupJobVolumesModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        backup_mode = EAgentBackupJobMode(d.pop("backupMode"))

        storage = AgentBackupPolicyStorageModel.from_dict(d.pop("storage"))

        _computers = d.pop("computers", UNSET)
        computers: list[AgentObjectModel] | Unset = UNSET
        if _computers is not UNSET:
            computers = []
            for computers_item_data in _computers:
                computers_item = AgentObjectModel.from_dict(computers_item_data)

                computers.append(computers_item)

        use_snapshotless_file_level_backup = d.pop("useSnapshotlessFileLevelBackup", UNSET)

        _volumes = d.pop("volumes", UNSET)
        volumes: LinuxAgentBackupJobVolumesModel | Unset
        if isinstance(_volumes, Unset):
            volumes = UNSET
        else:
            volumes = LinuxAgentBackupJobVolumesModel.from_dict(_volumes)

        _files = d.pop("files", UNSET)
        files: LinuxAgentBackupJobFilesModel | Unset
        if isinstance(_files, Unset):
            files = UNSET
        else:
            files = LinuxAgentBackupJobFilesModel.from_dict(_files)

        _guest_processing = d.pop("guestProcessing", UNSET)
        guest_processing: LinuxAgentBackupJobGuestProcessingModel | Unset
        if isinstance(_guest_processing, Unset):
            guest_processing = UNSET
        else:
            guest_processing = LinuxAgentBackupJobGuestProcessingModel.from_dict(_guest_processing)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        linux_agent_management_backup_server_policy_spec = cls(
            name=name,
            type_=type_,
            description=description,
            backup_mode=backup_mode,
            storage=storage,
            computers=computers,
            use_snapshotless_file_level_backup=use_snapshotless_file_level_backup,
            volumes=volumes,
            files=files,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        linux_agent_management_backup_server_policy_spec.additional_properties = d
        return linux_agent_management_backup_server_policy_spec

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
