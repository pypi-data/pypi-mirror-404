from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_allowed_backups_type import EAllowedBackupsType

T = TypeVar("T", bound="BackupPlacementSettingsModel")


@_attrs_define
class BackupPlacementSettingsModel:
    """
    Attributes:
        extent_id (UUID): ID of a performance extent.
        allowed_backups (EAllowedBackupsType): Type of backup files that can be stored on the extent.
    """

    extent_id: UUID
    allowed_backups: EAllowedBackupsType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        extent_id = str(self.extent_id)

        allowed_backups = self.allowed_backups.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "extentId": extent_id,
                "allowedBackups": allowed_backups,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        extent_id = UUID(d.pop("extentId"))

        allowed_backups = EAllowedBackupsType(d.pop("allowedBackups"))

        backup_placement_settings_model = cls(
            extent_id=extent_id,
            allowed_backups=allowed_backups,
        )

        backup_placement_settings_model.additional_properties = d
        return backup_placement_settings_model

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
