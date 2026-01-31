from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryImportOptions")


@_attrs_define
class RepositoryImportOptions:
    """Repository import options.

    Attributes:
        import_backup (bool | Unset): If `true`, Veeam Backup & Replication will search the repository for existing
            backups and import them automatically.
        import_index (bool | Unset): If `true`, Veeam Backup & Replication will import the guest OS file system index.
    """

    import_backup: bool | Unset = UNSET
    import_index: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        import_backup = self.import_backup

        import_index = self.import_index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if import_backup is not UNSET:
            field_dict["importBackup"] = import_backup
        if import_index is not UNSET:
            field_dict["importIndex"] = import_index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        import_backup = d.pop("importBackup", UNSET)

        import_index = d.pop("importIndex", UNSET)

        repository_import_options = cls(
            import_backup=import_backup,
            import_index=import_index,
        )

        repository_import_options.additional_properties = d
        return repository_import_options

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
