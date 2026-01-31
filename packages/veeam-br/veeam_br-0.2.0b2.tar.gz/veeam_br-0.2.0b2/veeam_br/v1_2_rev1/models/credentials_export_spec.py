from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CredentialsExportSpec")


@_attrs_define
class CredentialsExportSpec:
    """
    Attributes:
        show_hidden_creds (bool | Unset): If `true`, service credentials are exported.
        ids (list[UUID] | Unset): Array of credentials IDs.
        types (list[ECredentialsType] | Unset): Array of credentials types.
        names (list[str] | Unset): Array of credentials user names. Wildcard characters are supported.
    """

    show_hidden_creds: bool | Unset = UNSET
    ids: list[UUID] | Unset = UNSET
    types: list[ECredentialsType] | Unset = UNSET
    names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        show_hidden_creds = self.show_hidden_creds

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
        if show_hidden_creds is not UNSET:
            field_dict["showHiddenCreds"] = show_hidden_creds
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
        show_hidden_creds = d.pop("showHiddenCreds", UNSET)

        _ids = d.pop("ids", UNSET)
        ids: list[UUID] | Unset = UNSET
        if _ids is not UNSET:
            ids = []
            for ids_item_data in _ids:
                ids_item = UUID(ids_item_data)

                ids.append(ids_item)

        _types = d.pop("types", UNSET)
        types: list[ECredentialsType] | Unset = UNSET
        if _types is not UNSET:
            types = []
            for types_item_data in _types:
                types_item = ECredentialsType(types_item_data)

                types.append(types_item)

        names = cast(list[str], d.pop("names", UNSET))

        credentials_export_spec = cls(
            show_hidden_creds=show_hidden_creds,
            ids=ids,
            types=types,
            names=names,
        )

        credentials_export_spec.additional_properties = d
        return credentials_export_spec

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
