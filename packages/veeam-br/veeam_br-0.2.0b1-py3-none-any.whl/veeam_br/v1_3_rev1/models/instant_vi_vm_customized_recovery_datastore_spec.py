from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="InstantViVMCustomizedRecoveryDatastoreSpec")


@_attrs_define
class InstantViVMCustomizedRecoveryDatastoreSpec:
    """Datastore that keeps redo logs with changes that take place while a VM is running from a backup. To get a datastore
    object, run the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.

        Attributes:
            redirect_enabled (bool): If `true`, redo logs are redirected to `cacheDatastore`.
            cache_datastore (InventoryObjectModel | Unset): Inventory object properties.
    """

    redirect_enabled: bool
    cache_datastore: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        redirect_enabled = self.redirect_enabled

        cache_datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cache_datastore, Unset):
            cache_datastore = self.cache_datastore.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "redirectEnabled": redirect_enabled,
            }
        )
        if cache_datastore is not UNSET:
            field_dict["cacheDatastore"] = cache_datastore

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        redirect_enabled = d.pop("redirectEnabled")

        _cache_datastore = d.pop("cacheDatastore", UNSET)
        cache_datastore: InventoryObjectModel | Unset
        if isinstance(_cache_datastore, Unset):
            cache_datastore = UNSET
        else:
            cache_datastore = InventoryObjectModel.from_dict(_cache_datastore)

        instant_vi_vm_customized_recovery_datastore_spec = cls(
            redirect_enabled=redirect_enabled,
            cache_datastore=cache_datastore,
        )

        instant_vi_vm_customized_recovery_datastore_spec.additional_properties = d
        return instant_vi_vm_customized_recovery_datastore_spec

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
