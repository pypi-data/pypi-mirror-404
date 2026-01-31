from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_machine_model import CloudMachineModel


T = TypeVar("T", bound="AzureMachinesBrowserModel")


@_attrs_define
class AzureMachinesBrowserModel:
    """Microsoft Azure virtual machines.

    Attributes:
        service_type (EProtectionGroupCloudAccountType): Cloud account type.
        region_type (EAzureRegionType | Unset): Microsoft Azure region.
        region (str | Unset): Region where the Microsoft Azure datacenter is located.
        subscription_id (UUID | Unset): Microsoft Azure subscription ID.
        virtual_machines (list[CloudMachineModel] | Unset): Array of Microsoft Azure virtual machines.
    """

    service_type: EProtectionGroupCloudAccountType
    region_type: EAzureRegionType | Unset = UNSET
    region: str | Unset = UNSET
    subscription_id: UUID | Unset = UNSET
    virtual_machines: list[CloudMachineModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_type = self.service_type.value

        region_type: str | Unset = UNSET
        if not isinstance(self.region_type, Unset):
            region_type = self.region_type.value

        region = self.region

        subscription_id: str | Unset = UNSET
        if not isinstance(self.subscription_id, Unset):
            subscription_id = str(self.subscription_id)

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
        if subscription_id is not UNSET:
            field_dict["subscriptionId"] = subscription_id
        if virtual_machines is not UNSET:
            field_dict["virtualMachines"] = virtual_machines

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_machine_model import CloudMachineModel

        d = dict(src_dict)
        service_type = EProtectionGroupCloudAccountType(d.pop("serviceType"))

        _region_type = d.pop("regionType", UNSET)
        region_type: EAzureRegionType | Unset
        if isinstance(_region_type, Unset):
            region_type = UNSET
        else:
            region_type = EAzureRegionType(_region_type)

        region = d.pop("region", UNSET)

        _subscription_id = d.pop("subscriptionId", UNSET)
        subscription_id: UUID | Unset
        if isinstance(_subscription_id, Unset):
            subscription_id = UNSET
        else:
            subscription_id = UUID(_subscription_id)

        _virtual_machines = d.pop("virtualMachines", UNSET)
        virtual_machines: list[CloudMachineModel] | Unset = UNSET
        if _virtual_machines is not UNSET:
            virtual_machines = []
            for virtual_machines_item_data in _virtual_machines:
                virtual_machines_item = CloudMachineModel.from_dict(virtual_machines_item_data)

                virtual_machines.append(virtual_machines_item)

        azure_machines_browser_model = cls(
            service_type=service_type,
            region_type=region_type,
            region=region,
            subscription_id=subscription_id,
            virtual_machines=virtual_machines,
        )

        azure_machines_browser_model.additional_properties = d
        return azure_machines_browser_model

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
