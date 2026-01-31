from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_name_model import AzureComputeNameModel
    from ..models.azure_compute_network_model import AzureComputeNetworkModel
    from ..models.azure_compute_resource_group_model import AzureComputeResourceGroupModel
    from ..models.azure_compute_subscription_model import AzureComputeSubscriptionModel
    from ..models.azure_compute_vm_size_model import AzureComputeVMSizeModel
    from ..models.azure_instant_vm_recovery_appliance_model import AzureInstantVMRecoveryApplianceModel


T = TypeVar("T", bound="AzureInstantVMRecoverySpec")


@_attrs_define
class AzureInstantVMRecoverySpec:
    """Settings for Instant Recovery to Azure.

    Attributes:
        restore_point_id (UUID): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        subscription (AzureComputeSubscriptionModel): Azure compute subscription.
        vm_size (AzureComputeVMSizeModel): Size settings for Microsoft Azure VM.
        resource_group (AzureComputeResourceGroupModel): Microsoft Azure resource group.
        network (AzureComputeNetworkModel): Microsoft Azure VM network settings.
        appliance (AzureInstantVMRecoveryApplianceModel): Helper appliance for Instant Recovery to Azure.
        name (AzureComputeNameModel | Unset): Name of Microsoft Azure VM.
        reason (str | Unset): Reason for performing Instant Recovery to Azure.
        verify_vm_boot (bool | Unset): If `true`, Veeam Backup & Replication will verify whether the restored VM has
            booted properly.
    """

    restore_point_id: UUID
    subscription: AzureComputeSubscriptionModel
    vm_size: AzureComputeVMSizeModel
    resource_group: AzureComputeResourceGroupModel
    network: AzureComputeNetworkModel
    appliance: AzureInstantVMRecoveryApplianceModel
    name: AzureComputeNameModel | Unset = UNSET
    reason: str | Unset = UNSET
    verify_vm_boot: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        subscription = self.subscription.to_dict()

        vm_size = self.vm_size.to_dict()

        resource_group = self.resource_group.to_dict()

        network = self.network.to_dict()

        appliance = self.appliance.to_dict()

        name: dict[str, Any] | Unset = UNSET
        if not isinstance(self.name, Unset):
            name = self.name.to_dict()

        reason = self.reason

        verify_vm_boot = self.verify_vm_boot

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "subscription": subscription,
                "vmSize": vm_size,
                "resourceGroup": resource_group,
                "network": network,
                "appliance": appliance,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if reason is not UNSET:
            field_dict["reason"] = reason
        if verify_vm_boot is not UNSET:
            field_dict["verifyVMBoot"] = verify_vm_boot

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_name_model import AzureComputeNameModel
        from ..models.azure_compute_network_model import AzureComputeNetworkModel
        from ..models.azure_compute_resource_group_model import AzureComputeResourceGroupModel
        from ..models.azure_compute_subscription_model import AzureComputeSubscriptionModel
        from ..models.azure_compute_vm_size_model import AzureComputeVMSizeModel
        from ..models.azure_instant_vm_recovery_appliance_model import AzureInstantVMRecoveryApplianceModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        subscription = AzureComputeSubscriptionModel.from_dict(d.pop("subscription"))

        vm_size = AzureComputeVMSizeModel.from_dict(d.pop("vmSize"))

        resource_group = AzureComputeResourceGroupModel.from_dict(d.pop("resourceGroup"))

        network = AzureComputeNetworkModel.from_dict(d.pop("network"))

        appliance = AzureInstantVMRecoveryApplianceModel.from_dict(d.pop("appliance"))

        _name = d.pop("name", UNSET)
        name: AzureComputeNameModel | Unset
        if isinstance(_name, Unset):
            name = UNSET
        else:
            name = AzureComputeNameModel.from_dict(_name)

        reason = d.pop("reason", UNSET)

        verify_vm_boot = d.pop("verifyVMBoot", UNSET)

        azure_instant_vm_recovery_spec = cls(
            restore_point_id=restore_point_id,
            subscription=subscription,
            vm_size=vm_size,
            resource_group=resource_group,
            network=network,
            appliance=appliance,
            name=name,
            reason=reason,
            verify_vm_boot=verify_vm_boot,
        )

        azure_instant_vm_recovery_spec.additional_properties = d
        return azure_instant_vm_recovery_spec

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
