from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SuspiciousActivityMachineModel")


@_attrs_define
class SuspiciousActivityMachineModel:
    """Machine marked by the malware event.

    Attributes:
        display_name (str): Machine name.
        uuid (str): Machine BIOS UUID.
        backup_object_id (UUID): Backup object ID.
    """

    display_name: str
    uuid: str
    backup_object_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        uuid = self.uuid

        backup_object_id = str(self.backup_object_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "displayName": display_name,
                "uuid": uuid,
                "backupObjectId": backup_object_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName")

        uuid = d.pop("uuid")

        backup_object_id = UUID(d.pop("backupObjectId"))

        suspicious_activity_machine_model = cls(
            display_name=display_name,
            uuid=uuid,
            backup_object_id=backup_object_id,
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
