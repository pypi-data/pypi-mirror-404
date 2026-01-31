from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_restore_type import EFlrRestoreType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrRestoreSpec")


@_attrs_define
class FlrRestoreSpec:
    """Settings for restoring files and folders to the original location.

    Attributes:
        source_path (list[str]): Array of paths to the items that you want to restore.
        restore_type (EFlrRestoreType): Restore type.
        credentials_id (UUID | Unset): ID of a credentials record used to connect to the target machine. Allowed only
            for Linux machines.
        target_path (str | Unset): Path to the target folder.
    """

    source_path: list[str]
    restore_type: EFlrRestoreType
    credentials_id: UUID | Unset = UNSET
    target_path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_path = self.source_path

        restore_type = self.restore_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        target_path = self.target_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourcePath": source_path,
                "restoreType": restore_type,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if target_path is not UNSET:
            field_dict["targetPath"] = target_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_path = cast(list[str], d.pop("sourcePath"))

        restore_type = EFlrRestoreType(d.pop("restoreType"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        target_path = d.pop("targetPath", UNSET)

        flr_restore_spec = cls(
            source_path=source_path,
            restore_type=restore_type,
            credentials_id=credentials_id,
            target_path=target_path,
        )

        flr_restore_spec.additional_properties = d
        return flr_restore_spec

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
