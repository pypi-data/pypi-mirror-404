from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_replica_failback_type import EReplicaFailbackType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackSpec:
    """Failback settings of VMware vSphere snapshot replicas.

    Attributes:
        type_ (EReplicaFailbackType): Failback type.<ul><li>`OriginalLocation` — Failback to the original VM that
            resides in the original location</li><li>`OriginalVM` — Failback to the original VM that was restored to a
            different location</li><li>`Customized` — Failback to a custom location</li></ul>
        replica_point_ids (list[UUID] | Unset): Array of replica restore points that you want to fail back from.
        dr_site_proxy_id (list[UUID] | Unset): Array of backup proxies in the disaster recovery site.
        production_site_proxy_id (list[UUID] | Unset): Array of backup proxies in the production site.
        power_on_target_vm (bool | Unset): If `true`, the target VMs will be powered on right after the failback.
    """

    type_: EReplicaFailbackType
    replica_point_ids: list[UUID] | Unset = UNSET
    dr_site_proxy_id: list[UUID] | Unset = UNSET
    production_site_proxy_id: list[UUID] | Unset = UNSET
    power_on_target_vm: bool | Unset = UNSET
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        vi_vm_snapshot_replica_failback_spec = cls(
            type_=type_,
            replica_point_ids=replica_point_ids,
            dr_site_proxy_id=dr_site_proxy_id,
            production_site_proxy_id=production_site_proxy_id,
            power_on_target_vm=power_on_target_vm,
        )

        vi_vm_snapshot_replica_failback_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_spec

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
