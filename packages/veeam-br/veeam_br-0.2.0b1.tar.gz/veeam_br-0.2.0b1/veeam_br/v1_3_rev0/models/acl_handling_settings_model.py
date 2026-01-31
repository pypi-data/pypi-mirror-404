from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eacl_handling_backup_mode import EACLHandlingBackupMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="ACLHandlingSettingsModel")


@_attrs_define
class ACLHandlingSettingsModel:
    """ACL handling settings.

    Attributes:
        backup_mode (EACLHandlingBackupMode | Unset): ACL handling backup mode. The selected option determines whether
            the backup job will process permissions and attributes of folders only (recommended), or from both folders and
            individual files (slower).
    """

    backup_mode: EACLHandlingBackupMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_mode: str | Unset = UNSET
        if not isinstance(self.backup_mode, Unset):
            backup_mode = self.backup_mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_mode is not UNSET:
            field_dict["backupMode"] = backup_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _backup_mode = d.pop("backupMode", UNSET)
        backup_mode: EACLHandlingBackupMode | Unset
        if isinstance(_backup_mode, Unset):
            backup_mode = UNSET
        else:
            backup_mode = EACLHandlingBackupMode(_backup_mode)

        acl_handling_settings_model = cls(
            backup_mode=backup_mode,
        )

        acl_handling_settings_model.additional_properties = d
        return acl_handling_settings_model

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
