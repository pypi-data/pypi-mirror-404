from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureLinuxHelperApplianceSpec")


@_attrs_define
class AzureLinuxHelperApplianceSpec:
    """Settings for Linux-based helper appliance.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        subscription_id (UUID): ID that Veeam Backup & Replication assigned to the Microsoft Azure subscription.
        location (str | Unset): Storage account location where you want to configure the helper appliance.
        storage_account (str | Unset): Name of the Microsoft Azure storage account whose resources are used to store the
            helper appliance.
        resource_group (str | Unset): Resource group associated with the helper appliance.
        virtual_network (str | Unset): Network to which the helper appliance is connected.
        subnet (str | Unset): Subnet for the helper appliance.
        ssh_port (int | Unset): Port over which Veeam Backup & Replication communicates with the helper appliance.
    """

    type_: ECloudCredentialsType
    subscription_id: UUID
    location: str | Unset = UNSET
    storage_account: str | Unset = UNSET
    resource_group: str | Unset = UNSET
    virtual_network: str | Unset = UNSET
    subnet: str | Unset = UNSET
    ssh_port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        subscription_id = str(self.subscription_id)

        location = self.location

        storage_account = self.storage_account

        resource_group = self.resource_group

        virtual_network = self.virtual_network

        subnet = self.subnet

        ssh_port = self.ssh_port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "subscriptionId": subscription_id,
            }
        )
        if location is not UNSET:
            field_dict["location"] = location
        if storage_account is not UNSET:
            field_dict["storageAccount"] = storage_account
        if resource_group is not UNSET:
            field_dict["resourceGroup"] = resource_group
        if virtual_network is not UNSET:
            field_dict["virtualNetwork"] = virtual_network
        if subnet is not UNSET:
            field_dict["subnet"] = subnet
        if ssh_port is not UNSET:
            field_dict["SSHPort"] = ssh_port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        subscription_id = UUID(d.pop("subscriptionId"))

        location = d.pop("location", UNSET)

        storage_account = d.pop("storageAccount", UNSET)

        resource_group = d.pop("resourceGroup", UNSET)

        virtual_network = d.pop("virtualNetwork", UNSET)

        subnet = d.pop("subnet", UNSET)

        ssh_port = d.pop("SSHPort", UNSET)

        azure_linux_helper_appliance_spec = cls(
            type_=type_,
            subscription_id=subscription_id,
            location=location,
            storage_account=storage_account,
            resource_group=resource_group,
            virtual_network=virtual_network,
            subnet=subnet,
            ssh_port=ssh_port,
        )

        azure_linux_helper_appliance_spec.additional_properties = d
        return azure_linux_helper_appliance_spec

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
