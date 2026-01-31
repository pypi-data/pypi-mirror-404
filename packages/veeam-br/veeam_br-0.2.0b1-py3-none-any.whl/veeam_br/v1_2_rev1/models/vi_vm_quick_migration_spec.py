from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ViVMQuickMigrationSpec")


@_attrs_define
class ViVMQuickMigrationSpec:
    """
    Attributes:
        destination_host (InventoryObjectModel): Inventory object properties.
        resource_pool (InventoryObjectModel | Unset): Inventory object properties.
        folder (InventoryObjectModel | Unset): Inventory object properties.
        datastore (InventoryObjectModel | Unset): Inventory object properties.
        source_proxy_ids (list[UUID] | Unset): Array of source backup proxies.
        target_proxy_ids (list[UUID] | Unset): Array of target backup proxies.
        veeam_qm_enabled (bool | Unset): If `true`, the Veeam Quick Migration mechanism is used. Otherwise, Veeam Backup
            & Replication will use VMware vMotion for migration.
        delete_source_vms_files (bool | Unset): If `true`, Veeam Backup & Replication will delete source VM files upon
            successful migration.
    """

    destination_host: InventoryObjectModel
    resource_pool: InventoryObjectModel | Unset = UNSET
    folder: InventoryObjectModel | Unset = UNSET
    datastore: InventoryObjectModel | Unset = UNSET
    source_proxy_ids: list[UUID] | Unset = UNSET
    target_proxy_ids: list[UUID] | Unset = UNSET
    veeam_qm_enabled: bool | Unset = UNSET
    delete_source_vms_files: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        destination_host = self.destination_host.to_dict()

        resource_pool: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource_pool, Unset):
            resource_pool = self.resource_pool.to_dict()

        folder: dict[str, Any] | Unset = UNSET
        if not isinstance(self.folder, Unset):
            folder = self.folder.to_dict()

        datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.datastore, Unset):
            datastore = self.datastore.to_dict()

        source_proxy_ids: list[str] | Unset = UNSET
        if not isinstance(self.source_proxy_ids, Unset):
            source_proxy_ids = []
            for source_proxy_ids_item_data in self.source_proxy_ids:
                source_proxy_ids_item = str(source_proxy_ids_item_data)
                source_proxy_ids.append(source_proxy_ids_item)

        target_proxy_ids: list[str] | Unset = UNSET
        if not isinstance(self.target_proxy_ids, Unset):
            target_proxy_ids = []
            for target_proxy_ids_item_data in self.target_proxy_ids:
                target_proxy_ids_item = str(target_proxy_ids_item_data)
                target_proxy_ids.append(target_proxy_ids_item)

        veeam_qm_enabled = self.veeam_qm_enabled

        delete_source_vms_files = self.delete_source_vms_files

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "destinationHost": destination_host,
            }
        )
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool
        if folder is not UNSET:
            field_dict["folder"] = folder
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if source_proxy_ids is not UNSET:
            field_dict["sourceProxyIds"] = source_proxy_ids
        if target_proxy_ids is not UNSET:
            field_dict["targetProxyIds"] = target_proxy_ids
        if veeam_qm_enabled is not UNSET:
            field_dict["VeeamQMEnabled"] = veeam_qm_enabled
        if delete_source_vms_files is not UNSET:
            field_dict["DeleteSourceVmsFiles"] = delete_source_vms_files

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        destination_host = InventoryObjectModel.from_dict(d.pop("destinationHost"))

        _resource_pool = d.pop("resourcePool", UNSET)
        resource_pool: InventoryObjectModel | Unset
        if isinstance(_resource_pool, Unset):
            resource_pool = UNSET
        else:
            resource_pool = InventoryObjectModel.from_dict(_resource_pool)

        _folder = d.pop("folder", UNSET)
        folder: InventoryObjectModel | Unset
        if isinstance(_folder, Unset):
            folder = UNSET
        else:
            folder = InventoryObjectModel.from_dict(_folder)

        _datastore = d.pop("datastore", UNSET)
        datastore: InventoryObjectModel | Unset
        if isinstance(_datastore, Unset):
            datastore = UNSET
        else:
            datastore = InventoryObjectModel.from_dict(_datastore)

        _source_proxy_ids = d.pop("sourceProxyIds", UNSET)
        source_proxy_ids: list[UUID] | Unset = UNSET
        if _source_proxy_ids is not UNSET:
            source_proxy_ids = []
            for source_proxy_ids_item_data in _source_proxy_ids:
                source_proxy_ids_item = UUID(source_proxy_ids_item_data)

                source_proxy_ids.append(source_proxy_ids_item)

        _target_proxy_ids = d.pop("targetProxyIds", UNSET)
        target_proxy_ids: list[UUID] | Unset = UNSET
        if _target_proxy_ids is not UNSET:
            target_proxy_ids = []
            for target_proxy_ids_item_data in _target_proxy_ids:
                target_proxy_ids_item = UUID(target_proxy_ids_item_data)

                target_proxy_ids.append(target_proxy_ids_item)

        veeam_qm_enabled = d.pop("VeeamQMEnabled", UNSET)

        delete_source_vms_files = d.pop("DeleteSourceVmsFiles", UNSET)

        vi_vm_quick_migration_spec = cls(
            destination_host=destination_host,
            resource_pool=resource_pool,
            folder=folder,
            datastore=datastore,
            source_proxy_ids=source_proxy_ids,
            target_proxy_ids=target_proxy_ids,
            veeam_qm_enabled=veeam_qm_enabled,
            delete_source_vms_files=delete_source_vms_files,
        )

        vi_vm_quick_migration_spec.additional_properties = d
        return vi_vm_quick_migration_spec

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
