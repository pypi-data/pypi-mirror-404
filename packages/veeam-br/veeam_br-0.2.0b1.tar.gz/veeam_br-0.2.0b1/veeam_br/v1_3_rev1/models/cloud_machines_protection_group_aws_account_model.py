from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudMachinesProtectionGroupAWSAccountModel")


@_attrs_define
class CloudMachinesProtectionGroupAWSAccountModel:
    """AWS account of cloud machine added to the protection group.

    Attributes:
        account_type (EProtectionGroupCloudAccountType): Cloud account type.
        credentials_id (UUID): Credentials ID.
        region_type (EAmazonRegionType): AWS region type.
        region_id (str): ID of a region where the storage is located.
        assign_iam_role (bool | Unset): If `true`, IAM role will be auto-assigned to all machines without any existing
            IAM roles present.
    """

    account_type: EProtectionGroupCloudAccountType
    credentials_id: UUID
    region_type: EAmazonRegionType
    region_id: str
    assign_iam_role: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        account_type = self.account_type.value

        credentials_id = str(self.credentials_id)

        region_type = self.region_type.value

        region_id = self.region_id

        assign_iam_role = self.assign_iam_role

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accountType": account_type,
                "credentialsId": credentials_id,
                "regionType": region_type,
                "regionId": region_id,
            }
        )
        if assign_iam_role is not UNSET:
            field_dict["assignIamRole"] = assign_iam_role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_type = EProtectionGroupCloudAccountType(d.pop("accountType"))

        credentials_id = UUID(d.pop("credentialsId"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        region_id = d.pop("regionId")

        assign_iam_role = d.pop("assignIamRole", UNSET)

        cloud_machines_protection_group_aws_account_model = cls(
            account_type=account_type,
            credentials_id=credentials_id,
            region_type=region_type,
            region_id=region_id,
            assign_iam_role=assign_iam_role,
        )

        cloud_machines_protection_group_aws_account_model.additional_properties = d
        return cloud_machines_protection_group_aws_account_model

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
