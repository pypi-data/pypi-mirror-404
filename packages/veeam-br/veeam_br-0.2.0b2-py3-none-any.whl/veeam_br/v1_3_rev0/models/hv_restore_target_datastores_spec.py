from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hv_restore_target_datastore_spec import HvRestoreTargetDatastoreSpec


T = TypeVar("T", bound="HvRestoreTargetDatastoresSpec")


@_attrs_define
class HvRestoreTargetDatastoresSpec:
    """Destination datastore.

    Attributes:
        configuration_files_path (str | Unset): Absolute path where the configuration files should be placed on the
            target host.
        disk_mappings (list[HvRestoreTargetDatastoreSpec] | Unset): Array of disks and their locations in the target
            datastore. To get information about disks, use the [Get Inventory Objects](Inventory-
            Browser#operation/GetInventoryObjects) request with the `HostsAndVolumes` filter.
    """

    configuration_files_path: str | Unset = UNSET
    disk_mappings: list[HvRestoreTargetDatastoreSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        configuration_files_path = self.configuration_files_path

        disk_mappings: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disk_mappings, Unset):
            disk_mappings = []
            for disk_mappings_item_data in self.disk_mappings:
                disk_mappings_item = disk_mappings_item_data.to_dict()
                disk_mappings.append(disk_mappings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if configuration_files_path is not UNSET:
            field_dict["configurationFilesPath"] = configuration_files_path
        if disk_mappings is not UNSET:
            field_dict["diskMappings"] = disk_mappings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hv_restore_target_datastore_spec import HvRestoreTargetDatastoreSpec

        d = dict(src_dict)
        configuration_files_path = d.pop("configurationFilesPath", UNSET)

        _disk_mappings = d.pop("diskMappings", UNSET)
        disk_mappings: list[HvRestoreTargetDatastoreSpec] | Unset = UNSET
        if _disk_mappings is not UNSET:
            disk_mappings = []
            for disk_mappings_item_data in _disk_mappings:
                disk_mappings_item = HvRestoreTargetDatastoreSpec.from_dict(disk_mappings_item_data)

                disk_mappings.append(disk_mappings_item)

        hv_restore_target_datastores_spec = cls(
            configuration_files_path=configuration_files_path,
            disk_mappings=disk_mappings,
        )

        hv_restore_target_datastores_spec.additional_properties = d
        return hv_restore_target_datastores_spec

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
