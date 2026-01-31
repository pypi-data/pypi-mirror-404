from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_machines_protection_group_objects_model import CloudMachinesProtectionGroupObjectsModel


T = TypeVar("T", bound="CloudMachinesProtectionGroupExclusionsModel")


@_attrs_define
class CloudMachinesProtectionGroupExclusionsModel:
    """Exclusion settings for cloud objects.

    Attributes:
        exclude_selected_objects (bool | Unset): If `true`, the selected objects will be excluded from processing.
        excluded_objects (list[CloudMachinesProtectionGroupObjectsModel] | Unset): Array of excluded objects.
    """

    exclude_selected_objects: bool | Unset = UNSET
    excluded_objects: list[CloudMachinesProtectionGroupObjectsModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exclude_selected_objects = self.exclude_selected_objects

        excluded_objects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.excluded_objects, Unset):
            excluded_objects = []
            for excluded_objects_item_data in self.excluded_objects:
                excluded_objects_item = excluded_objects_item_data.to_dict()
                excluded_objects.append(excluded_objects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exclude_selected_objects is not UNSET:
            field_dict["excludeSelectedObjects"] = exclude_selected_objects
        if excluded_objects is not UNSET:
            field_dict["excludedObjects"] = excluded_objects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_machines_protection_group_objects_model import CloudMachinesProtectionGroupObjectsModel

        d = dict(src_dict)
        exclude_selected_objects = d.pop("excludeSelectedObjects", UNSET)

        _excluded_objects = d.pop("excludedObjects", UNSET)
        excluded_objects: list[CloudMachinesProtectionGroupObjectsModel] | Unset = UNSET
        if _excluded_objects is not UNSET:
            excluded_objects = []
            for excluded_objects_item_data in _excluded_objects:
                excluded_objects_item = CloudMachinesProtectionGroupObjectsModel.from_dict(excluded_objects_item_data)

                excluded_objects.append(excluded_objects_item)

        cloud_machines_protection_group_exclusions_model = cls(
            exclude_selected_objects=exclude_selected_objects,
            excluded_objects=excluded_objects,
        )

        cloud_machines_protection_group_exclusions_model.additional_properties = d
        return cloud_machines_protection_group_exclusions_model

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
