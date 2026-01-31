from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureStorageProxyModel")


@_attrs_define
class AzureStorageProxyModel:
    """Microsoft Azure storage proxy appliance.

    Attributes:
        subscription_id (UUID): ID that Veeam Backup & Replication assigned to the Microsoft Azure subscription.
        instance_size (str | Unset): Size of the appliance.
        resource_group (str | Unset): Resource group associated with the proxy appliance.
        virtual_network (str | Unset): Network to which the helper appliance is connected.
        subnet (str | Unset): Subnet for the proxy appliance.
        redirector_port (int | Unset): TCP port used to route requests between the proxy appliance and backup
            infrastructure components.
    """

    subscription_id: UUID
    instance_size: str | Unset = UNSET
    resource_group: str | Unset = UNSET
    virtual_network: str | Unset = UNSET
    subnet: str | Unset = UNSET
    redirector_port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscription_id = str(self.subscription_id)

        instance_size = self.instance_size

        resource_group = self.resource_group

        virtual_network = self.virtual_network

        subnet = self.subnet

        redirector_port = self.redirector_port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subscriptionId": subscription_id,
            }
        )
        if instance_size is not UNSET:
            field_dict["instanceSize"] = instance_size
        if resource_group is not UNSET:
            field_dict["resourceGroup"] = resource_group
        if virtual_network is not UNSET:
            field_dict["virtualNetwork"] = virtual_network
        if subnet is not UNSET:
            field_dict["subnet"] = subnet
        if redirector_port is not UNSET:
            field_dict["redirectorPort"] = redirector_port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subscription_id = UUID(d.pop("subscriptionId"))

        instance_size = d.pop("instanceSize", UNSET)

        resource_group = d.pop("resourceGroup", UNSET)

        virtual_network = d.pop("virtualNetwork", UNSET)

        subnet = d.pop("subnet", UNSET)

        redirector_port = d.pop("redirectorPort", UNSET)

        azure_storage_proxy_model = cls(
            subscription_id=subscription_id,
            instance_size=instance_size,
            resource_group=resource_group,
            virtual_network=virtual_network,
            subnet=subnet,
            redirector_port=redirector_port,
        )

        azure_storage_proxy_model.additional_properties = d
        return azure_storage_proxy_model

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
