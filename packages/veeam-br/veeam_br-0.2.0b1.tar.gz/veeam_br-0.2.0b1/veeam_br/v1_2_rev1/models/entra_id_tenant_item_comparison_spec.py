from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantItemComparisonSpec")


@_attrs_define
class EntraIdTenantItemComparisonSpec:
    """
    Attributes:
        item_id (str): ID of a Microsoft Entra ID item.
        item_type (EEntraIdTenantItemType): Item type.
        old_restore_point_id (UUID): ID of an earlier restore point.
        new_restore_point_id (UUID | Unset): ID of a later restore point. If you do not specify this property, the item
            from the earlir restore point will be compared to the item in production.
        show_unchanged_attributes (bool | Unset): If `true`, both changed and unchanged item properties are returned.
            Otherwise, only changed ones.
        reload_cache (bool | Unset): This property is only used when comparing the item to production
            (`newRestorePointId` must not be specified). <ul><li>If `true`, the mount session cache will be reset for this
            request and new data will be obtained from Microsoft Entra ID.</li> <li>If `false`, the data will be obtained
            from the cache.</li></ul> Resetting the cache slows down request processing but allows you to get up-to-date
            data. To check the time when the cache was last updated, use the `cacheTimestamp` property in the response body.
    """

    item_id: str
    item_type: EEntraIdTenantItemType
    old_restore_point_id: UUID
    new_restore_point_id: UUID | Unset = UNSET
    show_unchanged_attributes: bool | Unset = UNSET
    reload_cache: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_id = self.item_id

        item_type = self.item_type.value

        old_restore_point_id = str(self.old_restore_point_id)

        new_restore_point_id: str | Unset = UNSET
        if not isinstance(self.new_restore_point_id, Unset):
            new_restore_point_id = str(self.new_restore_point_id)

        show_unchanged_attributes = self.show_unchanged_attributes

        reload_cache = self.reload_cache

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "itemId": item_id,
                "itemType": item_type,
                "oldRestorePointId": old_restore_point_id,
            }
        )
        if new_restore_point_id is not UNSET:
            field_dict["newRestorePointId"] = new_restore_point_id
        if show_unchanged_attributes is not UNSET:
            field_dict["showUnchangedAttributes"] = show_unchanged_attributes
        if reload_cache is not UNSET:
            field_dict["reloadCache"] = reload_cache

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_id = d.pop("itemId")

        item_type = EEntraIdTenantItemType(d.pop("itemType"))

        old_restore_point_id = UUID(d.pop("oldRestorePointId"))

        _new_restore_point_id = d.pop("newRestorePointId", UNSET)
        new_restore_point_id: UUID | Unset
        if isinstance(_new_restore_point_id, Unset):
            new_restore_point_id = UNSET
        else:
            new_restore_point_id = UUID(_new_restore_point_id)

        show_unchanged_attributes = d.pop("showUnchangedAttributes", UNSET)

        reload_cache = d.pop("reloadCache", UNSET)

        entra_id_tenant_item_comparison_spec = cls(
            item_id=item_id,
            item_type=item_type,
            old_restore_point_id=old_restore_point_id,
            new_restore_point_id=new_restore_point_id,
            show_unchanged_attributes=show_unchanged_attributes,
            reload_cache=reload_cache,
        )

        entra_id_tenant_item_comparison_spec.additional_properties = d
        return entra_id_tenant_item_comparison_spec

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
