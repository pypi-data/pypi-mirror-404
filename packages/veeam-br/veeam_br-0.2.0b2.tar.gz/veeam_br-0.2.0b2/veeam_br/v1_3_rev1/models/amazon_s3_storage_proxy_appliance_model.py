from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonS3StorageProxyApplianceModel")


@_attrs_define
class AmazonS3StorageProxyApplianceModel:
    """Amazon S3 proxy appliance.

    Attributes:
        ec_2_instance_type (str | Unset): EC2 instance type for the proxy appliance.
        vpc_name (str | Unset): Name of the Amazon VPC where Veeam Backup & Replication launches the target instance.
        vpc_id (str | Unset): ID of the Amazon VPC where Veeam Backup & Replication launches the target instance. Use
            the ID to uniquely identify Amazon VPC.
        subnet_name (str | Unset): Name of the subnet for the proxy appliance.
        subnet_id (str | Unset): ID of the subnet for the proxy appliance. Use the ID to uniquely identify the subnet.
        security_group (str | Unset): Security group associated with the proxy appliance.
        redirector_port (int | Unset): TCP port used to route requests between the proxy appliance and backup
            infrastructure components.
    """

    ec_2_instance_type: str | Unset = UNSET
    vpc_name: str | Unset = UNSET
    vpc_id: str | Unset = UNSET
    subnet_name: str | Unset = UNSET
    subnet_id: str | Unset = UNSET
    security_group: str | Unset = UNSET
    redirector_port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ec_2_instance_type = self.ec_2_instance_type

        vpc_name = self.vpc_name

        vpc_id = self.vpc_id

        subnet_name = self.subnet_name

        subnet_id = self.subnet_id

        security_group = self.security_group

        redirector_port = self.redirector_port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ec_2_instance_type is not UNSET:
            field_dict["ec2InstanceType"] = ec_2_instance_type
        if vpc_name is not UNSET:
            field_dict["vpcName"] = vpc_name
        if vpc_id is not UNSET:
            field_dict["vpcId"] = vpc_id
        if subnet_name is not UNSET:
            field_dict["subnetName"] = subnet_name
        if subnet_id is not UNSET:
            field_dict["subnetId"] = subnet_id
        if security_group is not UNSET:
            field_dict["securityGroup"] = security_group
        if redirector_port is not UNSET:
            field_dict["redirectorPort"] = redirector_port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ec_2_instance_type = d.pop("ec2InstanceType", UNSET)

        vpc_name = d.pop("vpcName", UNSET)

        vpc_id = d.pop("vpcId", UNSET)

        subnet_name = d.pop("subnetName", UNSET)

        subnet_id = d.pop("subnetId", UNSET)

        security_group = d.pop("securityGroup", UNSET)

        redirector_port = d.pop("redirectorPort", UNSET)

        amazon_s3_storage_proxy_appliance_model = cls(
            ec_2_instance_type=ec_2_instance_type,
            vpc_name=vpc_name,
            vpc_id=vpc_id,
            subnet_name=subnet_name,
            subnet_id=subnet_id,
            security_group=security_group,
            redirector_port=redirector_port,
        )

        amazon_s3_storage_proxy_appliance_model.additional_properties = d
        return amazon_s3_storage_proxy_appliance_model

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
