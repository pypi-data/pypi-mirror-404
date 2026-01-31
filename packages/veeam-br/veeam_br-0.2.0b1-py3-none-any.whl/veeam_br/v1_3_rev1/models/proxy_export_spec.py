from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxy_type import EProxyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProxyExportSpec")


@_attrs_define
class ProxyExportSpec:
    """Proxy export settings.

    Attributes:
        ids (list[UUID] | Unset): Array of backup proxy IDs.
        types (list[EProxyType] | Unset): Array of backup proxy types.
        names (list[str] | Unset): Array of backup proxy names. Wildcard characters are supported.
    """

    ids: list[UUID] | Unset = UNSET
    types: list[EProxyType] | Unset = UNSET
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
            types = []
            for types_item_data in self.types:
                types_item = types_item_data.value
                types.append(types_item)

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

        _types = d.pop("types", UNSET)
        types: list[EProxyType] | Unset = UNSET
        if _types is not UNSET:
            types = []
            for types_item_data in _types:
                types_item = EProxyType(types_item_data)

                types.append(types_item)

        names = cast(list[str], d.pop("names", UNSET))

        proxy_export_spec = cls(
            ids=ids,
            types=types,
            names=names,
        )

        proxy_export_spec.additional_properties = d
        return proxy_export_spec

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
