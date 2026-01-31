from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instant_vm_recovery_mode_type import EInstantVMRecoveryModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hv_restore_target_datastores_spec import HvRestoreTargetDatastoresSpec
    from ..models.hv_restore_target_name_spec import HvRestoreTargetNameSpec
    from ..models.hv_restore_target_network_spec import HvRestoreTargetNetworkSpec
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.secure_restore_spec import SecureRestoreSpec


T = TypeVar("T", bound="InstantHvVMCustomizedRecoverySpec")


@_attrs_define
class InstantHvVMCustomizedRecoverySpec:
    """Instant Recovery to a new location or with different settings.

    Attributes:
        restore_point_id (UUID): ID of the restore point.
        type_ (EInstantVMRecoveryModeType): Instant Recovery restore mode.

            | Enum Value               | Description
            |
            |--------------------------|------------------------------------------------------------------------------------
            -------------------------------------------------------------------------------------|
            | OriginalLocation         | Veeam Backup & Replication will perform Instant Recovery to the original location.
            |
            | Customized               | Veeam Backup & Replication will perform Instant Recovery to a new location or to
            the original location with new settings.<br><br>Note: If you do not specify an optional property that defines
            target settings (such as VM name, destination host, resource pool, folder and so on), Veeam Backup & Replication
            will try to use the source settings for that property. |
        secure_restore (SecureRestoreSpec | Unset): Secure restore settings.
        power_up (bool | Unset): If `true`, Veeam Backup & Replication powers on the restored VM on the target host.
        reason (str | Unset): Reason for restoring the VM.
        destination_host (HyperVObjectModel | Unset): Microsoft Hyper-V object.
        datastore (HvRestoreTargetDatastoresSpec | Unset): Destination datastore.
        network (HvRestoreTargetNetworkSpec | Unset): Network to which the restored VM will be connected. To get
            information about source and target network objects, run the [Get Inventory Objects](Inventory-
            Browser#operation/GetInventoryObjects) request with the `Network` filter.
        target (HvRestoreTargetNameSpec | Unset): Destination VM folder.
    """

    restore_point_id: UUID
    type_: EInstantVMRecoveryModeType
    secure_restore: SecureRestoreSpec | Unset = UNSET
    power_up: bool | Unset = UNSET
    reason: str | Unset = UNSET
    destination_host: HyperVObjectModel | Unset = UNSET
    datastore: HvRestoreTargetDatastoresSpec | Unset = UNSET
    network: HvRestoreTargetNetworkSpec | Unset = UNSET
    target: HvRestoreTargetNameSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        secure_restore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.secure_restore, Unset):
            secure_restore = self.secure_restore.to_dict()

        power_up = self.power_up

        reason = self.reason

        destination_host: dict[str, Any] | Unset = UNSET
        if not isinstance(self.destination_host, Unset):
            destination_host = self.destination_host.to_dict()

        datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.datastore, Unset):
            datastore = self.datastore.to_dict()

        network: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network, Unset):
            network = self.network.to_dict()

        target: dict[str, Any] | Unset = UNSET
        if not isinstance(self.target, Unset):
            target = self.target.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
            }
        )
        if secure_restore is not UNSET:
            field_dict["secureRestore"] = secure_restore
        if power_up is not UNSET:
            field_dict["powerUp"] = power_up
        if reason is not UNSET:
            field_dict["reason"] = reason
        if destination_host is not UNSET:
            field_dict["destinationHost"] = destination_host
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if network is not UNSET:
            field_dict["network"] = network
        if target is not UNSET:
            field_dict["target"] = target

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hv_restore_target_datastores_spec import HvRestoreTargetDatastoresSpec
        from ..models.hv_restore_target_name_spec import HvRestoreTargetNameSpec
        from ..models.hv_restore_target_network_spec import HvRestoreTargetNetworkSpec
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.secure_restore_spec import SecureRestoreSpec

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EInstantVMRecoveryModeType(d.pop("type"))

        _secure_restore = d.pop("secureRestore", UNSET)
        secure_restore: SecureRestoreSpec | Unset
        if isinstance(_secure_restore, Unset):
            secure_restore = UNSET
        else:
            secure_restore = SecureRestoreSpec.from_dict(_secure_restore)

        power_up = d.pop("powerUp", UNSET)

        reason = d.pop("reason", UNSET)

        _destination_host = d.pop("destinationHost", UNSET)
        destination_host: HyperVObjectModel | Unset
        if isinstance(_destination_host, Unset):
            destination_host = UNSET
        else:
            destination_host = HyperVObjectModel.from_dict(_destination_host)

        _datastore = d.pop("datastore", UNSET)
        datastore: HvRestoreTargetDatastoresSpec | Unset
        if isinstance(_datastore, Unset):
            datastore = UNSET
        else:
            datastore = HvRestoreTargetDatastoresSpec.from_dict(_datastore)

        _network = d.pop("network", UNSET)
        network: HvRestoreTargetNetworkSpec | Unset
        if isinstance(_network, Unset):
            network = UNSET
        else:
            network = HvRestoreTargetNetworkSpec.from_dict(_network)

        _target = d.pop("target", UNSET)
        target: HvRestoreTargetNameSpec | Unset
        if isinstance(_target, Unset):
            target = UNSET
        else:
            target = HvRestoreTargetNameSpec.from_dict(_target)

        instant_hv_vm_customized_recovery_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            secure_restore=secure_restore,
            power_up=power_up,
            reason=reason,
            destination_host=destination_host,
            datastore=datastore,
            network=network,
            target=target,
        )

        instant_hv_vm_customized_recovery_spec.additional_properties = d
        return instant_hv_vm_customized_recovery_spec

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
