from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobExportSpec")


@_attrs_define
class JobExportSpec:
    """
    Attributes:
        ids (list[UUID] | Unset): Array of job IDs.
        types (list[str] | Unset): Array of job types.
        names (list[str] | Unset): Array of job names. Wildcard characters are supported.
    """

    ids: list[UUID] | Unset = UNSET
    types: list[str] | Unset = UNSET
    names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ids: list[str] | Unset = UNSET
        if not isinstance(self.ids, Unset):
            ids = []
            for ids_item_data in self.ids:
                ids_item = str(ids_item_data)
                ids.append(ids_item)

        types: list[str] | Unset = UNSET
        if not isinstance(self.types, Unset):
            types = self.types

        names: list[str] | Unset = UNSET
        if not isinstance(self.names, Unset):
            names = self.names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ids is not UNSET:
            field_dict["ids"] = ids
        if types is not UNSET:
            field_dict["types"] = types
        if names is not UNSET:
            field_dict["names"] = names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _ids = d.pop("ids", UNSET)
        ids: list[UUID] | Unset = UNSET
        if _ids is not UNSET:
            ids = []
            for ids_item_data in _ids:
                ids_item = UUID(ids_item_data)

                ids.append(ids_item)

        types = cast(list[str], d.pop("types", UNSET))

        names = cast(list[str], d.pop("names", UNSET))

        job_export_spec = cls(
            ids=ids,
            types=types,
            names=names,
        )

        job_export_spec.additional_properties = d
        return job_export_spec

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
