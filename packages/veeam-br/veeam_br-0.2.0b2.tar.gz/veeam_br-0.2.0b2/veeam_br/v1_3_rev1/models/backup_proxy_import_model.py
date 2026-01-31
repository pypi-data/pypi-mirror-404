from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_proxy_import_type import EBackupProxyImportType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupProxyImportModel")


@_attrs_define
class BackupProxyImportModel:
    """Backup proxy.

    Attributes:
        name (str): Name of the backup proxy.
        type_ (EBackupProxyImportType): Backup proxy type.
        unique_id (str | Unset): Unique ID assigned to the backup proxy.
    """

    name: str
    type_: EBackupProxyImportType
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        type_ = EBackupProxyImportType(d.pop("type"))

        unique_id = d.pop("uniqueId", UNSET)

        backup_proxy_import_model = cls(
            name=name,
            type_=type_,
            unique_id=unique_id,
        )

        backup_proxy_import_model.additional_properties = d
        return backup_proxy_import_model

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
