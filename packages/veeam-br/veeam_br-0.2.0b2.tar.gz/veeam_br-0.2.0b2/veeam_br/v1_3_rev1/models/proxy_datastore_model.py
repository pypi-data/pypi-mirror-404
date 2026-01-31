from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ProxyDatastoreModel")


@_attrs_define
class ProxyDatastoreModel:
    """Datastore to which the backup proxy has a direct SAN or NFS connection.

    Attributes:
        datastore (InventoryObjectModel | Unset): Inventory object properties.
        vm_count (int | Unset): Number of VMs.
    """

    datastore: InventoryObjectModel | Unset = UNSET
    vm_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.datastore, Unset):
            datastore = self.datastore.to_dict()

        vm_count = self.vm_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if vm_count is not UNSET:
            field_dict["vmCount"] = vm_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        _datastore = d.pop("datastore", UNSET)
        datastore: InventoryObjectModel | Unset
        if isinstance(_datastore, Unset):
            datastore = UNSET
        else:
            datastore = InventoryObjectModel.from_dict(_datastore)

        vm_count = d.pop("vmCount", UNSET)

        proxy_datastore_model = cls(
            datastore=datastore,
            vm_count=vm_count,
        )

        proxy_datastore_model.additional_properties = d
        return proxy_datastore_model

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
