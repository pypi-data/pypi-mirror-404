from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.v_sphere_replica_job_destination_files_mapping_model import (
        VSphereReplicaJobDestinationFilesMappingModel,
    )


T = TypeVar("T", bound="VSphereReplicaJobDestinationMappingModel")


@_attrs_define
class VSphereReplicaJobDestinationMappingModel:
    """Mapping rule.

    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        configuration_files_datastore_mapping (InventoryObjectModel): Inventory object properties.
        disk_files_mapping (list[VSphereReplicaJobDestinationFilesMappingModel] | Unset): Array of disk mapping rules
            (disk name, disk datastore and provisioning type).
    """

    vm_object: InventoryObjectModel
    configuration_files_datastore_mapping: InventoryObjectModel
    disk_files_mapping: list[VSphereReplicaJobDestinationFilesMappingModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        configuration_files_datastore_mapping = self.configuration_files_datastore_mapping.to_dict()

        disk_files_mapping: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disk_files_mapping, Unset):
            disk_files_mapping = []
            for disk_files_mapping_item_data in self.disk_files_mapping:
                disk_files_mapping_item = disk_files_mapping_item_data.to_dict()
                disk_files_mapping.append(disk_files_mapping_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
                "configurationFilesDatastoreMapping": configuration_files_datastore_mapping,
            }
        )
        if disk_files_mapping is not UNSET:
            field_dict["diskFilesMapping"] = disk_files_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.v_sphere_replica_job_destination_files_mapping_model import (
            VSphereReplicaJobDestinationFilesMappingModel,
        )

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        configuration_files_datastore_mapping = InventoryObjectModel.from_dict(
            d.pop("configurationFilesDatastoreMapping")
        )

        _disk_files_mapping = d.pop("diskFilesMapping", UNSET)
        disk_files_mapping: list[VSphereReplicaJobDestinationFilesMappingModel] | Unset = UNSET
        if _disk_files_mapping is not UNSET:
            disk_files_mapping = []
            for disk_files_mapping_item_data in _disk_files_mapping:
                disk_files_mapping_item = VSphereReplicaJobDestinationFilesMappingModel.from_dict(
                    disk_files_mapping_item_data
                )

                disk_files_mapping.append(disk_files_mapping_item)

        v_sphere_replica_job_destination_mapping_model = cls(
            vm_object=vm_object,
            configuration_files_datastore_mapping=configuration_files_datastore_mapping,
            disk_files_mapping=disk_files_mapping,
        )

        v_sphere_replica_job_destination_mapping_model.additional_properties = d
        return v_sphere_replica_job_destination_mapping_model

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
