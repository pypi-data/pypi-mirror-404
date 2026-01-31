from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.restore_target_datastore_spec import RestoreTargetDatastoreSpec


T = TypeVar("T", bound="RestoreTargetDatastoresSpec")


@_attrs_define
class RestoreTargetDatastoresSpec:
    """Destination datastore.

    Attributes:
        configuration_file_datastore (InventoryObjectModel | Unset): Inventory object properties.
        disk_mappings (list[RestoreTargetDatastoreSpec] | Unset):
    """

    configuration_file_datastore: InventoryObjectModel | Unset = UNSET
    disk_mappings: list[RestoreTargetDatastoreSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        configuration_file_datastore: dict[str, Any] | Unset = UNSET
        if not isinstance(self.configuration_file_datastore, Unset):
            configuration_file_datastore = self.configuration_file_datastore.to_dict()

        disk_mappings: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disk_mappings, Unset):
            disk_mappings = []
            for disk_mappings_item_data in self.disk_mappings:
                disk_mappings_item = disk_mappings_item_data.to_dict()
                disk_mappings.append(disk_mappings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if configuration_file_datastore is not UNSET:
            field_dict["configurationFileDatastore"] = configuration_file_datastore
        if disk_mappings is not UNSET:
            field_dict["diskMappings"] = disk_mappings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.restore_target_datastore_spec import RestoreTargetDatastoreSpec

        d = dict(src_dict)
        _configuration_file_datastore = d.pop("configurationFileDatastore", UNSET)
        configuration_file_datastore: InventoryObjectModel | Unset
        if isinstance(_configuration_file_datastore, Unset):
            configuration_file_datastore = UNSET
        else:
            configuration_file_datastore = InventoryObjectModel.from_dict(_configuration_file_datastore)

        _disk_mappings = d.pop("diskMappings", UNSET)
        disk_mappings: list[RestoreTargetDatastoreSpec] | Unset = UNSET
        if _disk_mappings is not UNSET:
            disk_mappings = []
            for disk_mappings_item_data in _disk_mappings:
                disk_mappings_item = RestoreTargetDatastoreSpec.from_dict(disk_mappings_item_data)

                disk_mappings.append(disk_mappings_item)

        restore_target_datastores_spec = cls(
            configuration_file_datastore=configuration_file_datastore,
            disk_mappings=disk_mappings,
        )

        restore_target_datastores_spec.additional_properties = d
        return restore_target_datastores_spec

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
