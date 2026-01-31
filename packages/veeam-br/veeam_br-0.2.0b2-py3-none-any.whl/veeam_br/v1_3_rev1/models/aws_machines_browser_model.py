from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_machine_model import CloudMachineModel


T = TypeVar("T", bound="AWSMachinesBrowserModel")


@_attrs_define
class AWSMachinesBrowserModel:
    """Amazon virtual machines.

    Attributes:
        service_type (EProtectionGroupCloudAccountType): Cloud account type.
        region_type (EAmazonRegionType | Unset): AWS region type.
        region (str | Unset): Region where the Amazon datacenter is located.
        credentials_id (UUID | Unset): Amazon credentials ID.
        virtual_machines (list[CloudMachineModel] | Unset): Amazon virtual machines.
    """

    service_type: EProtectionGroupCloudAccountType
    region_type: EAmazonRegionType | Unset = UNSET
    region: str | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    virtual_machines: list[CloudMachineModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_type = self.service_type.value

        region_type: str | Unset = UNSET
        if not isinstance(self.region_type, Unset):
            region_type = self.region_type.value

        region = self.region

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        virtual_machines: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.virtual_machines, Unset):
            virtual_machines = []
            for virtual_machines_item_data in self.virtual_machines:
                virtual_machines_item = virtual_machines_item_data.to_dict()
                virtual_machines.append(virtual_machines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serviceType": service_type,
            }
        )
        if region_type is not UNSET:
            field_dict["regionType"] = region_type
        if region is not UNSET:
            field_dict["region"] = region
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if virtual_machines is not UNSET:
            field_dict["virtualMachines"] = virtual_machines

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_machine_model import CloudMachineModel

        d = dict(src_dict)
        service_type = EProtectionGroupCloudAccountType(d.pop("serviceType"))

        _region_type = d.pop("regionType", UNSET)
        region_type: EAmazonRegionType | Unset
        if isinstance(_region_type, Unset):
            region_type = UNSET
        else:
            region_type = EAmazonRegionType(_region_type)

        region = d.pop("region", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _virtual_machines = d.pop("virtualMachines", UNSET)
        virtual_machines: list[CloudMachineModel] | Unset = UNSET
        if _virtual_machines is not UNSET:
            virtual_machines = []
            for virtual_machines_item_data in _virtual_machines:
                virtual_machines_item = CloudMachineModel.from_dict(virtual_machines_item_data)

                virtual_machines.append(virtual_machines_item)

        aws_machines_browser_model = cls(
            service_type=service_type,
            region_type=region_type,
            region=region,
            credentials_id=credentials_id,
            virtual_machines=virtual_machines,
        )

        aws_machines_browser_model.additional_properties = d
        return aws_machines_browser_model

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
