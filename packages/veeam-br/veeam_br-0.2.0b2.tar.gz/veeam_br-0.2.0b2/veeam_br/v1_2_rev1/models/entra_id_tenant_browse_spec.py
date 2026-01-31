from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantBrowseSpec")


@_attrs_define
class EntraIdTenantBrowseSpec:
    """
    Attributes:
        type_ (EEntraIdTenantItemType): Item type.
        skip (int | Unset): Number of items to skip.
        limit (int | Unset): Maximum number of items to return.
    """

    type_: EEntraIdTenantItemType
    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        skip = self.skip

        limit = self.limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EEntraIdTenantItemType(d.pop("type"))

        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        entra_id_tenant_browse_spec = cls(
            type_=type_,
            skip=skip,
            limit=limit,
        )

        entra_id_tenant_browse_spec.additional_properties = d
        return entra_id_tenant_browse_spec

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
