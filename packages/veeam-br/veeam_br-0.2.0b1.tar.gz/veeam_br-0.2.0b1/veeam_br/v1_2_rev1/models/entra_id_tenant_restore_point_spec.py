from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_restore_point_sorting_spec import EntraIdTenantRestorePointSortingSpec


T = TypeVar("T", bound="EntraIdTenantRestorePointSpec")


@_attrs_define
class EntraIdTenantRestorePointSpec:
    """
    Attributes:
        skip (int | Unset): Number of restore points to skip.
        limit (int | Unset): Maximum number of restore points to return.
        sorting (EntraIdTenantRestorePointSortingSpec | Unset): Sorting options.
    """

    skip: int | Unset = UNSET
    limit: int | Unset = UNSET
    sorting: EntraIdTenantRestorePointSortingSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        sorting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sorting, Unset):
            sorting = self.sorting.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit
        if sorting is not UNSET:
            field_dict["sorting"] = sorting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_restore_point_sorting_spec import EntraIdTenantRestorePointSortingSpec

        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _sorting = d.pop("sorting", UNSET)
        sorting: EntraIdTenantRestorePointSortingSpec | Unset
        if isinstance(_sorting, Unset):
            sorting = UNSET
        else:
            sorting = EntraIdTenantRestorePointSortingSpec.from_dict(_sorting)

        entra_id_tenant_restore_point_spec = cls(
            skip=skip,
            limit=limit,
            sorting=sorting,
        )

        entra_id_tenant_restore_point_spec.additional_properties = d
        return entra_id_tenant_restore_point_spec

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
