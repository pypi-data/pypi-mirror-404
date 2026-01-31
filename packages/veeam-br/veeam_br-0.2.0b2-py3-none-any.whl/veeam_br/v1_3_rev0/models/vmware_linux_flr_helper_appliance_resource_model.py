from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_platform_type import EFlrPlatformType

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VmwareLinuxFlrHelperApplianceResourceModel")


@_attrs_define
class VmwareLinuxFlrHelperApplianceResourceModel:
    """VMware vSphere settings&#58; ESXi host where the helper appliance must be registered, resource pool where the helper
    appliance must be placed, and network to which the helper appliance must be connected. To get the inventory objects,
    use the [Get All Servers](Inventory-Browser#operation/GetAllInventoryHosts) and [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects) requests.

        Attributes:
            type_ (EFlrPlatformType): Platform type.
            host (InventoryObjectModel): Inventory object properties.
            resource_pool (InventoryObjectModel): Inventory object properties.
            network (InventoryObjectModel): Inventory object properties.
    """

    type_: EFlrPlatformType
    host: InventoryObjectModel
    resource_pool: InventoryObjectModel
    network: InventoryObjectModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        host = self.host.to_dict()

        resource_pool = self.resource_pool.to_dict()

        network = self.network.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "host": host,
                "resourcePool": resource_pool,
                "network": network,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        type_ = EFlrPlatformType(d.pop("type"))

        host = InventoryObjectModel.from_dict(d.pop("host"))

        resource_pool = InventoryObjectModel.from_dict(d.pop("resourcePool"))

        network = InventoryObjectModel.from_dict(d.pop("network"))

        vmware_linux_flr_helper_appliance_resource_model = cls(
            type_=type_,
            host=host,
            resource_pool=resource_pool,
            network=network,
        )

        vmware_linux_flr_helper_appliance_resource_model.additional_properties = d
        return vmware_linux_flr_helper_appliance_resource_model

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
