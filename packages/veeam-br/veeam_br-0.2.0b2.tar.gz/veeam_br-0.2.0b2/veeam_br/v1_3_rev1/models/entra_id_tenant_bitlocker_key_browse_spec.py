from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_bitlocker_key_filter_browse_spec import EntraIdTenantBitlockerKeyFilterBrowseSpec
    from ..models.entra_id_tenant_bitlocker_key_sorting_browse_spec import EntraIdTenantBitlockerKeySortingBrowseSpec


T = TypeVar("T", bound="EntraIdTenantBitlockerKeyBrowseSpec")


@_attrs_define
class EntraIdTenantBitlockerKeyBrowseSpec:
    """Bitlocker recovery key settings.

    Attributes:
        type_ (EEntraIdTenantItemType): Item type.
        skip (int | Unset): Number of items to skip.
        limit (int | Unset): Maximum number of items to return.
        filter_ (EntraIdTenantBitlockerKeyFilterBrowseSpec | Unset):
        sorting (EntraIdTenantBitlockerKeySortingBrowseSpec | Unset): Settings for Bitlocker recovery key sorting.
    """

    type_: EEntraIdTenantItemType
    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    filter_: EntraIdTenantBitlockerKeyFilterBrowseSpec | Unset = UNSET
    sorting: EntraIdTenantBitlockerKeySortingBrowseSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        skip = self.skip

        limit = self.limit

        filter_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = self.filter_.to_dict()

        sorting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sorting, Unset):
            sorting = self.sorting.to_dict()

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
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if sorting is not UNSET:
            field_dict["sorting"] = sorting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_bitlocker_key_filter_browse_spec import EntraIdTenantBitlockerKeyFilterBrowseSpec
        from ..models.entra_id_tenant_bitlocker_key_sorting_browse_spec import (
            EntraIdTenantBitlockerKeySortingBrowseSpec,
        )

        d = dict(src_dict)
        type_ = EEntraIdTenantItemType(d.pop("type"))

        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _filter_ = d.pop("filter", UNSET)
        filter_: EntraIdTenantBitlockerKeyFilterBrowseSpec | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = EntraIdTenantBitlockerKeyFilterBrowseSpec.from_dict(_filter_)

        _sorting = d.pop("sorting", UNSET)
        sorting: EntraIdTenantBitlockerKeySortingBrowseSpec | Unset
        if isinstance(_sorting, Unset):
            sorting = UNSET
        else:
            sorting = EntraIdTenantBitlockerKeySortingBrowseSpec.from_dict(_sorting)

        entra_id_tenant_bitlocker_key_browse_spec = cls(
            type_=type_,
            skip=skip,
            limit=limit,
            filter_=filter_,
            sorting=sorting,
        )

        entra_id_tenant_bitlocker_key_browse_spec.additional_properties = d
        return entra_id_tenant_bitlocker_key_browse_spec

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
