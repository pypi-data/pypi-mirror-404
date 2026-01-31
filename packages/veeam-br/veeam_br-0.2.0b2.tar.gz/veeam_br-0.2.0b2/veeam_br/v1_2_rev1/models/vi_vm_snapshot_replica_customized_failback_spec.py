from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_replica_failback_type import EReplicaFailbackType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.replica_failback_mode_spec import ReplicaFailbackModeSpec
    from ..models.vi_vm_snapshot_replica_failback_target_datastore_spec import (
        ViVMSnapshotReplicaFailbackTargetDatastoreSpec,
    )
    from ..models.vi_vm_snapshot_replica_failback_target_folder_spec import ViVMSnapshotReplicaFailbackTargetFolderSpec
    from ..models.vi_vm_snapshot_replica_failback_target_host_spec import ViVMSnapshotReplicaFailbackTargetHostSpec
    from ..models.vi_vm_snapshot_replica_failback_target_network_spec import (
        ViVMSnapshotReplicaFailbackTargetNetworkSpec,
    )
    from ..models.vi_vm_snapshot_replica_failback_target_resource_pool_spec import (
        ViVMSnapshotReplicaFailbackTargetResourcePoolSpec,
    )


T = TypeVar("T", bound="ViVMSnapshotReplicaCustomizedFailbackSpec")


@_attrs_define
class ViVMSnapshotReplicaCustomizedFailbackSpec:
    """
    Attributes:
        type_ (EReplicaFailbackType): Failback type.<ul><li>`OriginalLocation` — Failback to the original VM that
            resides in the original location</li><li>`OriginalVM` — Failback to the original VM that was restored to a
            different location</li><li>`Customized` — Failback to a custom location</li></ul>
        replica_point_ids (list[UUID] | Unset): Array of replica restore points that you want to fail back from.
        dr_site_proxy_id (list[UUID] | Unset): Array of backup proxies in the disaster recovery site.
        production_site_proxy_id (list[UUID] | Unset): Array of backup proxies in the production site.
        power_on_target_vm (bool | Unset): If `true`, the target VMs will be powered on right after the failback.
        destinationhost (list[ViVMSnapshotReplicaFailbackTargetHostSpec] | Unset): Array of restore points and target
            hosts (or clusters) where the replicas will be registered. To get the inventory objects, use the [Get All
            Servers](#tag/Inventory-Browser/operation/GetAllInventoryHosts) and [Get Inventory Objects](#tag/Inventory-
            Browser/operation/GetInventoryObjects) requests.
        resource_pool (list[ViVMSnapshotReplicaFailbackTargetResourcePoolSpec] | Unset): Array of restore points and
            target resource pools. To get a resource pool object, use the [Get Inventory Objects](#tag/Inventory-
            Browser/operation/GetInventoryObjects) request.
        datastore (list[ViVMSnapshotReplicaFailbackTargetDatastoreSpec] | Unset): Array of datastores where
            configuration files and disk files of recovered VMs will be stored. To get a datastore object, use the [Get
            Inventory Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.
        folder (ViVMSnapshotReplicaFailbackTargetFolderSpec | Unset): Folders in the target datastores where all files
            of the recovered VMs will be stored.
        network (list[ViVMSnapshotReplicaFailbackTargetNetworkSpec] | Unset): Array of restore point and network mapping
            rules.
        failback_mode (ReplicaFailbackModeSpec | Unset): Failback mode.
    """

    type_: EReplicaFailbackType
    replica_point_ids: list[UUID] | Unset = UNSET
    dr_site_proxy_id: list[UUID] | Unset = UNSET
    production_site_proxy_id: list[UUID] | Unset = UNSET
    power_on_target_vm: bool | Unset = UNSET
    destinationhost: list[ViVMSnapshotReplicaFailbackTargetHostSpec] | Unset = UNSET
    resource_pool: list[ViVMSnapshotReplicaFailbackTargetResourcePoolSpec] | Unset = UNSET
    datastore: list[ViVMSnapshotReplicaFailbackTargetDatastoreSpec] | Unset = UNSET
    folder: ViVMSnapshotReplicaFailbackTargetFolderSpec | Unset = UNSET
    network: list[ViVMSnapshotReplicaFailbackTargetNetworkSpec] | Unset = UNSET
    failback_mode: ReplicaFailbackModeSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        replica_point_ids: list[str] | Unset = UNSET
        if not isinstance(self.replica_point_ids, Unset):
            replica_point_ids = []
            for replica_point_ids_item_data in self.replica_point_ids:
                replica_point_ids_item = str(replica_point_ids_item_data)
                replica_point_ids.append(replica_point_ids_item)

        dr_site_proxy_id: list[str] | Unset = UNSET
        if not isinstance(self.dr_site_proxy_id, Unset):
            dr_site_proxy_id = []
            for dr_site_proxy_id_item_data in self.dr_site_proxy_id:
                dr_site_proxy_id_item = str(dr_site_proxy_id_item_data)
                dr_site_proxy_id.append(dr_site_proxy_id_item)

        production_site_proxy_id: list[str] | Unset = UNSET
        if not isinstance(self.production_site_proxy_id, Unset):
            production_site_proxy_id = []
            for production_site_proxy_id_item_data in self.production_site_proxy_id:
                production_site_proxy_id_item = str(production_site_proxy_id_item_data)
                production_site_proxy_id.append(production_site_proxy_id_item)

        power_on_target_vm = self.power_on_target_vm

        destinationhost: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.destinationhost, Unset):
            destinationhost = []
            for destinationhost_item_data in self.destinationhost:
                destinationhost_item = destinationhost_item_data.to_dict()
                destinationhost.append(destinationhost_item)

        resource_pool: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.resource_pool, Unset):
            resource_pool = []
            for resource_pool_item_data in self.resource_pool:
                resource_pool_item = resource_pool_item_data.to_dict()
                resource_pool.append(resource_pool_item)

        datastore: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.datastore, Unset):
            datastore = []
            for datastore_item_data in self.datastore:
                datastore_item = datastore_item_data.to_dict()
                datastore.append(datastore_item)

        folder: dict[str, Any] | Unset = UNSET
        if not isinstance(self.folder, Unset):
            folder = self.folder.to_dict()

        network: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.network, Unset):
            network = []
            for network_item_data in self.network:
                network_item = network_item_data.to_dict()
                network.append(network_item)

        failback_mode: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failback_mode, Unset):
            failback_mode = self.failback_mode.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if replica_point_ids is not UNSET:
            field_dict["replicaPointIds"] = replica_point_ids
        if dr_site_proxy_id is not UNSET:
            field_dict["drSiteProxyId"] = dr_site_proxy_id
        if production_site_proxy_id is not UNSET:
            field_dict["productionSiteProxyId"] = production_site_proxy_id
        if power_on_target_vm is not UNSET:
            field_dict["powerOnTargetVM"] = power_on_target_vm
        if destinationhost is not UNSET:
            field_dict["destinationhost"] = destinationhost
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if folder is not UNSET:
            field_dict["folder"] = folder
        if network is not UNSET:
            field_dict["network"] = network
        if failback_mode is not UNSET:
            field_dict["failbackMode"] = failback_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.replica_failback_mode_spec import ReplicaFailbackModeSpec
        from ..models.vi_vm_snapshot_replica_failback_target_datastore_spec import (
            ViVMSnapshotReplicaFailbackTargetDatastoreSpec,
        )
        from ..models.vi_vm_snapshot_replica_failback_target_folder_spec import (
            ViVMSnapshotReplicaFailbackTargetFolderSpec,
        )
        from ..models.vi_vm_snapshot_replica_failback_target_host_spec import ViVMSnapshotReplicaFailbackTargetHostSpec
        from ..models.vi_vm_snapshot_replica_failback_target_network_spec import (
            ViVMSnapshotReplicaFailbackTargetNetworkSpec,
        )
        from ..models.vi_vm_snapshot_replica_failback_target_resource_pool_spec import (
            ViVMSnapshotReplicaFailbackTargetResourcePoolSpec,
        )

        d = dict(src_dict)
        type_ = EReplicaFailbackType(d.pop("type"))

        _replica_point_ids = d.pop("replicaPointIds", UNSET)
        replica_point_ids: list[UUID] | Unset = UNSET
        if _replica_point_ids is not UNSET:
            replica_point_ids = []
            for replica_point_ids_item_data in _replica_point_ids:
                replica_point_ids_item = UUID(replica_point_ids_item_data)

                replica_point_ids.append(replica_point_ids_item)

        _dr_site_proxy_id = d.pop("drSiteProxyId", UNSET)
        dr_site_proxy_id: list[UUID] | Unset = UNSET
        if _dr_site_proxy_id is not UNSET:
            dr_site_proxy_id = []
            for dr_site_proxy_id_item_data in _dr_site_proxy_id:
                dr_site_proxy_id_item = UUID(dr_site_proxy_id_item_data)

                dr_site_proxy_id.append(dr_site_proxy_id_item)

        _production_site_proxy_id = d.pop("productionSiteProxyId", UNSET)
        production_site_proxy_id: list[UUID] | Unset = UNSET
        if _production_site_proxy_id is not UNSET:
            production_site_proxy_id = []
            for production_site_proxy_id_item_data in _production_site_proxy_id:
                production_site_proxy_id_item = UUID(production_site_proxy_id_item_data)

                production_site_proxy_id.append(production_site_proxy_id_item)

        power_on_target_vm = d.pop("powerOnTargetVM", UNSET)

        _destinationhost = d.pop("destinationhost", UNSET)
        destinationhost: list[ViVMSnapshotReplicaFailbackTargetHostSpec] | Unset = UNSET
        if _destinationhost is not UNSET:
            destinationhost = []
            for destinationhost_item_data in _destinationhost:
                destinationhost_item = ViVMSnapshotReplicaFailbackTargetHostSpec.from_dict(destinationhost_item_data)

                destinationhost.append(destinationhost_item)

        _resource_pool = d.pop("resourcePool", UNSET)
        resource_pool: list[ViVMSnapshotReplicaFailbackTargetResourcePoolSpec] | Unset = UNSET
        if _resource_pool is not UNSET:
            resource_pool = []
            for resource_pool_item_data in _resource_pool:
                resource_pool_item = ViVMSnapshotReplicaFailbackTargetResourcePoolSpec.from_dict(
                    resource_pool_item_data
                )

                resource_pool.append(resource_pool_item)

        _datastore = d.pop("datastore", UNSET)
        datastore: list[ViVMSnapshotReplicaFailbackTargetDatastoreSpec] | Unset = UNSET
        if _datastore is not UNSET:
            datastore = []
            for datastore_item_data in _datastore:
                datastore_item = ViVMSnapshotReplicaFailbackTargetDatastoreSpec.from_dict(datastore_item_data)

                datastore.append(datastore_item)

        _folder = d.pop("folder", UNSET)
        folder: ViVMSnapshotReplicaFailbackTargetFolderSpec | Unset
        if isinstance(_folder, Unset):
            folder = UNSET
        else:
            folder = ViVMSnapshotReplicaFailbackTargetFolderSpec.from_dict(_folder)

        _network = d.pop("network", UNSET)
        network: list[ViVMSnapshotReplicaFailbackTargetNetworkSpec] | Unset = UNSET
        if _network is not UNSET:
            network = []
            for network_item_data in _network:
                network_item = ViVMSnapshotReplicaFailbackTargetNetworkSpec.from_dict(network_item_data)

                network.append(network_item)

        _failback_mode = d.pop("failbackMode", UNSET)
        failback_mode: ReplicaFailbackModeSpec | Unset
        if isinstance(_failback_mode, Unset):
            failback_mode = UNSET
        else:
            failback_mode = ReplicaFailbackModeSpec.from_dict(_failback_mode)

        vi_vm_snapshot_replica_customized_failback_spec = cls(
            type_=type_,
            replica_point_ids=replica_point_ids,
            dr_site_proxy_id=dr_site_proxy_id,
            production_site_proxy_id=production_site_proxy_id,
            power_on_target_vm=power_on_target_vm,
            destinationhost=destinationhost,
            resource_pool=resource_pool,
            datastore=datastore,
            folder=folder,
            network=network,
            failback_mode=failback_mode,
        )

        vi_vm_snapshot_replica_customized_failback_spec.additional_properties = d
        return vi_vm_snapshot_replica_customized_failback_spec

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
