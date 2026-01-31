from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="EntireCloudDirectorVMRestoreLocationModel")


@_attrs_define
class EntireCloudDirectorVMRestoreLocationModel:
    """Target location settings. To get a vApp object, use the [Get Inventory Objects](#tag/Inventory-
    Browser/operation/GetInventoryObjects) request.

        Attributes:
            new_name (str): New VM name.
            v_app (InventoryObjectModel): Inventory object properties.
            restore_v_sphere_vm_tags (bool): If `true`, VMware vSphere tags will be restored for this VM.
    """

    new_name: str
    v_app: InventoryObjectModel
    restore_v_sphere_vm_tags: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_name = self.new_name

        v_app = self.v_app.to_dict()

        restore_v_sphere_vm_tags = self.restore_v_sphere_vm_tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "newName": new_name,
                "vApp": v_app,
                "restoreVSphereVMTags": restore_v_sphere_vm_tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        new_name = d.pop("newName")

        v_app = InventoryObjectModel.from_dict(d.pop("vApp"))

        restore_v_sphere_vm_tags = d.pop("restoreVSphereVMTags")

        entire_cloud_director_vm_restore_location_model = cls(
            new_name=new_name,
            v_app=v_app,
            restore_v_sphere_vm_tags=restore_v_sphere_vm_tags,
        )

        entire_cloud_director_vm_restore_location_model.additional_properties = d
        return entire_cloud_director_vm_restore_location_model

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
