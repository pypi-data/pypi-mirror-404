from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entire_vm_restore_mode_type import EEntireVMRestoreModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_restore_target_datastore_spec import CloudDirectorRestoreTargetDatastoreSpec
    from ..models.entire_cloud_director_vm_restore_location_model import EntireCloudDirectorVMRestoreLocationModel
    from ..models.restore_proxy_spec import RestoreProxySpec
    from ..models.restore_target_network_spec import RestoreTargetNetworkSpec
    from ..models.secure_restore_spec import SecureRestoreSpec


T = TypeVar("T", bound="EntireCloudDirectorVMCustomizedRestoreSpec")


@_attrs_define
class EntireCloudDirectorVMCustomizedRestoreSpec:
    """Restore to a new location or with different settings.

    Attributes:
        restore_point_id (UUID): ID of the restore point.
        type_ (EEntireVMRestoreModeType): Entire VM restore mode.

            | Enum Value               | Description
            |
            |--------------------------|------------------------------------------------------------------------------------
            -------------------------------------------------------------------------------------|
            | OriginalLocation         | Veeam Backup & Replication will restore the entire VM to the original location.
            |
            | Customized               | Veeam Backup & Replication will restore the entire VM to a new location or to the
            original location with new settings.<br><br>Note: If you do not specify an optional property that defines target
            settings (such as VM name, destination host, resource pool, datastore, folder or network), Veeam Backup &
            Replication will try to use the source settings for that property. |
        location (EntireCloudDirectorVMRestoreLocationModel): Target location settings. To get a vApp object, run the
            [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
        restore_proxies (RestoreProxySpec | Unset): Backup proxies for VM data transport.
        secure_restore (SecureRestoreSpec | Unset): Secure restore settings.
        power_up (bool | Unset): If `true`, Veeam Backup & Replication powers on the restored VM on the target host.
        reason (str | Unset): Reason for restoring the VM.
        network (RestoreTargetNetworkSpec | Unset): Network to which the restored VM will be connected. To get a network
            object, run the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
        datastore (CloudDirectorRestoreTargetDatastoreSpec | Unset): Datastore and storage for the recovered VM. To get
            datastore and storage policy objects, run the [Get Inventory Objects](Inventory-
            Browser#operation/GetInventoryObjects) request.
    """

    restore_point_id: UUID
    type_: EEntireVMRestoreModeType
    location: EntireCloudDirectorVMRestoreLocationModel
    restore_proxies: RestoreProxySpec | Unset = UNSET
    secure_restore: SecureRestoreSpec | Unset = UNSET
    power_up: bool | Unset = UNSET
    reason: str | Unset = UNSET
    network: RestoreTargetNetworkSpec | Unset = UNSET
    datastore: CloudDirectorRestoreTargetDatastoreSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        location = self.location.to_dict()

        restore_proxies: dict[str, Any] | Unset = UNSET
        if not isinstance(self.restore_proxies, Unset):
            restore_proxies = self.restore_proxies.to_dict()

        secure_restore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.secure_restore, Unset):
            secure_restore = self.secure_restore.to_dict()

        power_up = self.power_up

        reason = self.reason

        network: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network, Unset):
            network = self.network.to_dict()

        datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.datastore, Unset):
            datastore = self.datastore.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
                "location": location,
            }
        )
        if restore_proxies is not UNSET:
            field_dict["restoreProxies"] = restore_proxies
        if secure_restore is not UNSET:
            field_dict["secureRestore"] = secure_restore
        if power_up is not UNSET:
            field_dict["powerUp"] = power_up
        if reason is not UNSET:
            field_dict["reason"] = reason
        if network is not UNSET:
            field_dict["network"] = network
        if datastore is not UNSET:
            field_dict["datastore"] = datastore

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_restore_target_datastore_spec import CloudDirectorRestoreTargetDatastoreSpec
        from ..models.entire_cloud_director_vm_restore_location_model import EntireCloudDirectorVMRestoreLocationModel
        from ..models.restore_proxy_spec import RestoreProxySpec
        from ..models.restore_target_network_spec import RestoreTargetNetworkSpec
        from ..models.secure_restore_spec import SecureRestoreSpec

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EEntireVMRestoreModeType(d.pop("type"))

        location = EntireCloudDirectorVMRestoreLocationModel.from_dict(d.pop("location"))

        _restore_proxies = d.pop("restoreProxies", UNSET)
        restore_proxies: RestoreProxySpec | Unset
        if isinstance(_restore_proxies, Unset):
            restore_proxies = UNSET
        else:
            restore_proxies = RestoreProxySpec.from_dict(_restore_proxies)

        _secure_restore = d.pop("secureRestore", UNSET)
        secure_restore: SecureRestoreSpec | Unset
        if isinstance(_secure_restore, Unset):
            secure_restore = UNSET
        else:
            secure_restore = SecureRestoreSpec.from_dict(_secure_restore)

        power_up = d.pop("powerUp", UNSET)

        reason = d.pop("reason", UNSET)

        _network = d.pop("network", UNSET)
        network: RestoreTargetNetworkSpec | Unset
        if isinstance(_network, Unset):
            network = UNSET
        else:
            network = RestoreTargetNetworkSpec.from_dict(_network)

        _datastore = d.pop("datastore", UNSET)
        datastore: CloudDirectorRestoreTargetDatastoreSpec | Unset
        if isinstance(_datastore, Unset):
            datastore = UNSET
        else:
            datastore = CloudDirectorRestoreTargetDatastoreSpec.from_dict(_datastore)

        entire_cloud_director_vm_customized_restore_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            location=location,
            restore_proxies=restore_proxies,
            secure_restore=secure_restore,
            power_up=power_up,
            reason=reason,
            network=network,
            datastore=datastore,
        )

        entire_cloud_director_vm_customized_restore_spec.additional_properties = d
        return entire_cloud_director_vm_customized_restore_spec

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
