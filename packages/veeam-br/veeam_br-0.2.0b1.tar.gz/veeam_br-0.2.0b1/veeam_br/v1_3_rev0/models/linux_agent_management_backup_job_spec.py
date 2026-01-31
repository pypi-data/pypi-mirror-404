from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_backup_job_mode import EAgentBackupJobMode
from ..models.e_job_agent_type import EJobAgentType
from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_job_storage_model import AgentBackupJobStorageModel
    from ..models.agent_object_model import AgentObjectModel
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.linux_agent_backup_job_files_model import LinuxAgentBackupJobFilesModel
    from ..models.linux_agent_backup_job_guest_processing_model import LinuxAgentBackupJobGuestProcessingModel
    from ..models.linux_agent_backup_job_volumes_model import LinuxAgentBackupJobVolumesModel


T = TypeVar("T", bound="LinuxAgentManagementBackupJobSpec")


@_attrs_define
class LinuxAgentManagementBackupJobSpec:
    """Settings for Veeam Agent for Linux backup jobs.

    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        computers (list[AgentObjectModel]): Array of computers included in the backup job.
        backup_mode (EAgentBackupJobMode): Backup job mode. Indicates the scope of the data you want to back up.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job over other similar jobs
            and allocates resources to it first.
        agent_type (EJobAgentType | Unset): Protected computer type.
        use_snapshotless_file_level_backup (bool | Unset): If `true`, the backup job will create a crash-consistent
            file-level backup without a snapshot. Available for the `FileLevel` backup mode only.
        volumes (LinuxAgentBackupJobVolumesModel | Unset): Details on volume objects.
        files (LinuxAgentBackupJobFilesModel | Unset): Backup scope settings for Veeam Agent for Linux backup jobs.
        storage (AgentBackupJobStorageModel | Unset): Storage settings.
        guest_processing (LinuxAgentBackupJobGuestProcessingModel | Unset): Guest processing settings for Veeam Agent
            for Linux backup job.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    name: str
    type_: EJobType
    description: str
    computers: list[AgentObjectModel]
    backup_mode: EAgentBackupJobMode
    is_high_priority: bool | Unset = UNSET
    agent_type: EJobAgentType | Unset = UNSET
    use_snapshotless_file_level_backup: bool | Unset = UNSET
    volumes: LinuxAgentBackupJobVolumesModel | Unset = UNSET
    files: LinuxAgentBackupJobFilesModel | Unset = UNSET
    storage: AgentBackupJobStorageModel | Unset = UNSET
    guest_processing: LinuxAgentBackupJobGuestProcessingModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        description = self.description

        computers = []
        for computers_item_data in self.computers:
            computers_item = computers_item_data.to_dict()
            computers.append(computers_item)

        backup_mode = self.backup_mode.value

        is_high_priority = self.is_high_priority

        agent_type: str | Unset = UNSET
        if not isinstance(self.agent_type, Unset):
            agent_type = self.agent_type.value

        use_snapshotless_file_level_backup = self.use_snapshotless_file_level_backup

        volumes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.volumes, Unset):
            volumes = self.volumes.to_dict()

        files: dict[str, Any] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = self.files.to_dict()

        storage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage, Unset):
            storage = self.storage.to_dict()

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
                "computers": computers,
                "backupMode": backup_mode,
            }
        )
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if agent_type is not UNSET:
            field_dict["agentType"] = agent_type
        if use_snapshotless_file_level_backup is not UNSET:
            field_dict["useSnapshotlessFileLevelBackup"] = use_snapshotless_file_level_backup
        if volumes is not UNSET:
            field_dict["volumes"] = volumes
        if files is not UNSET:
            field_dict["files"] = files
        if storage is not UNSET:
            field_dict["storage"] = storage
        if guest_processing is not UNSET:
            field_dict["guestProcessing"] = guest_processing
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_job_storage_model import AgentBackupJobStorageModel
        from ..models.agent_object_model import AgentObjectModel
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.linux_agent_backup_job_files_model import LinuxAgentBackupJobFilesModel
        from ..models.linux_agent_backup_job_guest_processing_model import LinuxAgentBackupJobGuestProcessingModel
        from ..models.linux_agent_backup_job_volumes_model import LinuxAgentBackupJobVolumesModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        computers = []
        _computers = d.pop("computers")
        for computers_item_data in _computers:
            computers_item = AgentObjectModel.from_dict(computers_item_data)

            computers.append(computers_item)

        backup_mode = EAgentBackupJobMode(d.pop("backupMode"))

        is_high_priority = d.pop("isHighPriority", UNSET)

        _agent_type = d.pop("agentType", UNSET)
        agent_type: EJobAgentType | Unset
        if isinstance(_agent_type, Unset):
            agent_type = UNSET
        else:
            agent_type = EJobAgentType(_agent_type)

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

        _storage = d.pop("storage", UNSET)
        storage: AgentBackupJobStorageModel | Unset
        if isinstance(_storage, Unset):
            storage = UNSET
        else:
            storage = AgentBackupJobStorageModel.from_dict(_storage)

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

        linux_agent_management_backup_job_spec = cls(
            name=name,
            type_=type_,
            description=description,
            computers=computers,
            backup_mode=backup_mode,
            is_high_priority=is_high_priority,
            agent_type=agent_type,
            use_snapshotless_file_level_backup=use_snapshotless_file_level_backup,
            volumes=volumes,
            files=files,
            storage=storage,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        linux_agent_management_backup_job_spec.additional_properties = d
        return linux_agent_management_backup_job_spec

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
