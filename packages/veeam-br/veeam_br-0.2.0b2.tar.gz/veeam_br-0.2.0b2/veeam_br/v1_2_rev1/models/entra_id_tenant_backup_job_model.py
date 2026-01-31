from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.entra_id_tenant_backup_job_storage_model import EntraIDTenantBackupJobStorageModel


T = TypeVar("T", bound="EntraIDTenantBackupJobModel")


@_attrs_define
class EntraIDTenantBackupJobModel:
    """Microsoft Entra ID tenant backup job.

    Attributes:
        id (UUID): ID of the job.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        is_disabled (bool): If `true`, the job is disabled.
        description (str): Description of the job.
        storage (EntraIDTenantBackupJobStorageModel): Job storage settings.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    id: UUID
    name: str
    type_: EJobType
    is_disabled: bool
    description: str
    storage: EntraIDTenantBackupJobStorageModel
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        is_disabled = self.is_disabled

        description = self.description

        storage = self.storage.to_dict()

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
                "storage": storage,
            }
        )
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.entra_id_tenant_backup_job_storage_model import EntraIDTenantBackupJobStorageModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        description = d.pop("description")

        storage = EntraIDTenantBackupJobStorageModel.from_dict(d.pop("storage"))

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        entra_id_tenant_backup_job_model = cls(
            id=id,
            name=name,
            type_=type_,
            is_disabled=is_disabled,
            description=description,
            storage=storage,
            schedule=schedule,
        )

        entra_id_tenant_backup_job_model.additional_properties = d
        return entra_id_tenant_backup_job_model

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
