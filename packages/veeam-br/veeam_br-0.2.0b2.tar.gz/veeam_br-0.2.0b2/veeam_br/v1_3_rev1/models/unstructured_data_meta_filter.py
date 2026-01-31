from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_meta_migration_type import EUnstructuredDataMetaMigrationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataMetaFilter")


@_attrs_define
class UnstructuredDataMetaFilter:
    """Metadata migration filter.

    Attributes:
        migration_type (EUnstructuredDataMetaMigrationType | Unset): Metadata migration type.
    """

    migration_type: EUnstructuredDataMetaMigrationType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        migration_type: str | Unset = UNSET
        if not isinstance(self.migration_type, Unset):
            migration_type = self.migration_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if migration_type is not UNSET:
            field_dict["migrationType"] = migration_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _migration_type = d.pop("migrationType", UNSET)
        migration_type: EUnstructuredDataMetaMigrationType | Unset
        if isinstance(_migration_type, Unset):
            migration_type = UNSET
        else:
            migration_type = EUnstructuredDataMetaMigrationType(_migration_type)

        unstructured_data_meta_filter = cls(
            migration_type=migration_type,
        )

        unstructured_data_meta_filter.additional_properties = d
        return unstructured_data_meta_filter

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
