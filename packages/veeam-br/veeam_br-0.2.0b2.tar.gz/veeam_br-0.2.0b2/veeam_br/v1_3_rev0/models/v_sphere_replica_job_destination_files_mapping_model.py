from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_disk_creation_mode import EDiskCreationMode

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VSphereReplicaJobDestinationFilesMappingModel")


@_attrs_define
class VSphereReplicaJobDestinationFilesMappingModel:
    """Disk mapping rule.

    Attributes:
        disk_name (str): Disk name.
        datastore (InventoryObjectModel): Inventory object properties.
        disk_type (EDiskCreationMode): Disk provisioning type for the recovered VM.
    """

    disk_name: str
    datastore: InventoryObjectModel
    disk_type: EDiskCreationMode
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disk_name = self.disk_name

        datastore = self.datastore.to_dict()

        disk_type = self.disk_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "diskName": disk_name,
                "datastore": datastore,
                "diskType": disk_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        disk_name = d.pop("diskName")

        datastore = InventoryObjectModel.from_dict(d.pop("datastore"))

        disk_type = EDiskCreationMode(d.pop("diskType"))

        v_sphere_replica_job_destination_files_mapping_model = cls(
            disk_name=disk_name,
            datastore=datastore,
            disk_type=disk_type,
        )

        v_sphere_replica_job_destination_files_mapping_model.additional_properties = d
        return v_sphere_replica_job_destination_files_mapping_model

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
