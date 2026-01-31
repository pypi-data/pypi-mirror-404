from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="CloudDirectorRestoreTargetDatastoreSpec")


@_attrs_define
class CloudDirectorRestoreTargetDatastoreSpec:
    """Datastore and storage for the recovered VM. To get datastore and storage policy objects, use the [Get Inventory
    Objects](Inventory-Browser#operation/GetInventoryObjects) request.

        Attributes:
            datastore (InventoryObjectModel): Inventory object properties.
            storage_policy (InventoryObjectModel | Unset): Inventory object properties.
    """

    datastore: InventoryObjectModel
    storage_policy: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datastore = self.datastore.to_dict()

        storage_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_policy, Unset):
            storage_policy = self.storage_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datastore": datastore,
            }
        )
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        datastore = InventoryObjectModel.from_dict(d.pop("datastore"))

        _storage_policy = d.pop("storagePolicy", UNSET)
        storage_policy: InventoryObjectModel | Unset
        if isinstance(_storage_policy, Unset):
            storage_policy = UNSET
        else:
            storage_policy = InventoryObjectModel.from_dict(_storage_policy)

        cloud_director_restore_target_datastore_spec = cls(
            datastore=datastore,
            storage_policy=storage_policy,
        )

        cloud_director_restore_target_datastore_spec.additional_properties = d
        return cloud_director_restore_target_datastore_spec

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
