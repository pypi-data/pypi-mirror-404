from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_backup_job_mode import EAgentBackupJobMode
from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_policy_storage_model import AgentBackupPolicyStorageModel
    from ..models.agent_object_model import AgentObjectModel
    from ..models.windows_agent_backup_job_files_model import WindowsAgentBackupJobFilesModel
    from ..models.windows_agent_backup_job_guest_processing_model import WindowsAgentBackupJobGuestProcessingModel
    from ..models.windows_agent_backup_job_volumes_model import WindowsAgentBackupJobVolumesModel
    from ..models.windows_agent_backup_policy_workstation_schedule_model import (
        WindowsAgentBackupPolicyWorkstationScheduleModel,
    )


T = TypeVar("T", bound="WindowsAgentManagementBackupWorkstationPolicyModel")


@_attrs_define
class WindowsAgentManagementBackupWorkstationPolicyModel:
    """Backup policy settings for Veeam Agent for Microsoft Windows. The settings apply to the `workstation` protected
    computer type.

        Attributes:
            id (UUID): Job ID.
            name (str): Name of the job.
            type_ (EJobType): Type of the job.
            is_disabled (bool): If `true`, the job is disabled.
            description (str): Description of the job.
            backup_mode (EAgentBackupJobMode): Backup job mode. Indicates the scope of the data you want to back up.
            storage (AgentBackupPolicyStorageModel): Backup policy storage settings
            computers (list[AgentObjectModel] | Unset): Array of protected computers.
            include_usb_drives (bool | Unset): If `true`, Veeam Agent will include in the backup all external USB drives
                that are connected to the Veeam Agent computer at the time when the backup policy starts.
            volumes (WindowsAgentBackupJobVolumesModel | Unset): Scope of volumes protected by the Veeam Agent for Microsoft
                Windows backup job.
            files (WindowsAgentBackupJobFilesModel | Unset): Backup scope settings for Veeam Agent for Microsoft Windows
                backup job.
            guest_processing (WindowsAgentBackupJobGuestProcessingModel | Unset): Guest processing settings.
            schedule (WindowsAgentBackupPolicyWorkstationScheduleModel | Unset): Schedule for the backup policy of Microsoft
                Windows workstations.
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    description: str
    backup_mode: EAgentBackupJobMode
    storage: AgentBackupPolicyStorageModel
    computers: list[AgentObjectModel] | Unset = UNSET
    include_usb_drives: bool | Unset = UNSET
    volumes: WindowsAgentBackupJobVolumesModel | Unset = UNSET
    files: WindowsAgentBackupJobFilesModel | Unset = UNSET
    guest_processing: WindowsAgentBackupJobGuestProcessingModel | Unset = UNSET
    schedule: WindowsAgentBackupPolicyWorkstationScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        description = self.description

        backup_mode = self.backup_mode.value

        storage = self.storage.to_dict()

        computers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.computers, Unset):
            computers = []
            for computers_item_data in self.computers:
                computers_item = computers_item_data.to_dict()
                computers.append(computers_item)

        include_usb_drives = self.include_usb_drives

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
                "id": id,
                "name": name,
                "type": type_,
                "isDisabled": is_disabled,
                "description": description,
                "backupMode": backup_mode,
                "storage": storage,
            }
        )
        if computers is not UNSET:
            field_dict["computers"] = computers
        if include_usb_drives is not UNSET:
            field_dict["includeUsbDrives"] = include_usb_drives
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
        from ..models.windows_agent_backup_job_files_model import WindowsAgentBackupJobFilesModel
        from ..models.windows_agent_backup_job_guest_processing_model import WindowsAgentBackupJobGuestProcessingModel
        from ..models.windows_agent_backup_job_volumes_model import WindowsAgentBackupJobVolumesModel
        from ..models.windows_agent_backup_policy_workstation_schedule_model import (
            WindowsAgentBackupPolicyWorkstationScheduleModel,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

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

        include_usb_drives = d.pop("includeUsbDrives", UNSET)

        _volumes = d.pop("volumes", UNSET)
        volumes: WindowsAgentBackupJobVolumesModel | Unset
        if isinstance(_volumes, Unset):
            volumes = UNSET
        else:
            volumes = WindowsAgentBackupJobVolumesModel.from_dict(_volumes)

        _files = d.pop("files", UNSET)
        files: WindowsAgentBackupJobFilesModel | Unset
        if isinstance(_files, Unset):
            files = UNSET
        else:
            files = WindowsAgentBackupJobFilesModel.from_dict(_files)

        _guest_processing = d.pop("guestProcessing", UNSET)
        guest_processing: WindowsAgentBackupJobGuestProcessingModel | Unset
        if isinstance(_guest_processing, Unset):
            guest_processing = UNSET
        else:
            guest_processing = WindowsAgentBackupJobGuestProcessingModel.from_dict(_guest_processing)

        _schedule = d.pop("schedule", UNSET)
        schedule: WindowsAgentBackupPolicyWorkstationScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = WindowsAgentBackupPolicyWorkstationScheduleModel.from_dict(_schedule)

        windows_agent_management_backup_workstation_policy_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
            description=description,
            backup_mode=backup_mode,
            storage=storage,
            computers=computers,
            include_usb_drives=include_usb_drives,
            volumes=volumes,
            files=files,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        windows_agent_management_backup_workstation_policy_model.additional_properties = d
        return windows_agent_management_backup_workstation_policy_model

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
