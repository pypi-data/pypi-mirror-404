from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SuspiciousActivityMachineModel")


@_attrs_define
class SuspiciousActivityMachineModel:
    """Machine marked by the malware event.

    Attributes:
        display_name (str): Machine name.
        uuid (str): Machine BIOS UUID.
        backup_object_id (UUID): Backup object ID of the machine.
        restore_point_id (UUID | Unset): Restore point ID of the backed up machine.
    """

    display_name: str
    uuid: str
    backup_object_id: UUID
    restore_point_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        uuid = self.uuid

        backup_object_id = str(self.backup_object_id)

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "displayName": display_name,
                "uuid": uuid,
                "backupObjectId": backup_object_id,
            }
        )
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName")

        uuid = d.pop("uuid")

        backup_object_id = UUID(d.pop("backupObjectId"))

        _restore_point_id = d.pop("restorePointId", UNSET)
        restore_point_id: UUID | Unset
        if isinstance(_restore_point_id, Unset):
            restore_point_id = UNSET
        else:
            restore_point_id = UUID(_restore_point_id)

        suspicious_activity_machine_model = cls(
            display_name=display_name,
            uuid=uuid,
            backup_object_id=backup_object_id,
            restore_point_id=restore_point_id,
        )

        suspicious_activity_machine_model.additional_properties = d
        return suspicious_activity_machine_model

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
