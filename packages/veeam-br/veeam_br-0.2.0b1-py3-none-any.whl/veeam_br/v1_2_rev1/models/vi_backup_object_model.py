from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_platform_type import EPlatformType
from ..models.e_vmware_inventory_type import EVmwareInventoryType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ViBackupObjectModel")


@_attrs_define
class ViBackupObjectModel:
    """
    Attributes:
        id (UUID): ID of the object.
        platform_name (EPlatformType): Platform type.
        object_id (str): ID of the virtual infrastructure object (mo-ref or ID, depending on the virtualization
            platform).
        name (str | Unset): Name of the object.
        type_ (str | Unset): Type of the object.
        platform_id (UUID | Unset): ID of the platform where the object was created. The value is always
            *00000000-0000-0000-0000-000000000000* except for custom platforms.
        restore_points_count (int | Unset): Number of restore points.
        vi_type (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note that inventory objects with
            multiple tags (*Multitag* type) can only be added in the Veeam Backup & Replication UI or PowerShell.
        path (str | Unset): Path to the object.
    """

    id: UUID
    platform_name: EPlatformType
    object_id: str
    name: str | Unset = UNSET
    type_: str | Unset = UNSET
    platform_id: UUID | Unset = UNSET
    restore_points_count: int | Unset = UNSET
    vi_type: EVmwareInventoryType | Unset = UNSET
    path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        platform_name = self.platform_name.value

        object_id = self.object_id

        name = self.name

        type_ = self.type_

        platform_id: str | Unset = UNSET
        if not isinstance(self.platform_id, Unset):
            platform_id = str(self.platform_id)

        restore_points_count = self.restore_points_count

        vi_type: str | Unset = UNSET
        if not isinstance(self.vi_type, Unset):
            vi_type = self.vi_type.value

        path = self.path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "platformName": platform_name,
                "objectId": object_id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if platform_id is not UNSET:
            field_dict["platformId"] = platform_id
        if restore_points_count is not UNSET:
            field_dict["restorePointsCount"] = restore_points_count
        if vi_type is not UNSET:
            field_dict["viType"] = vi_type
        if path is not UNSET:
            field_dict["path"] = path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        platform_name = EPlatformType(d.pop("platformName"))

        object_id = d.pop("objectId")

        name = d.pop("name", UNSET)

        type_ = d.pop("type", UNSET)

        _platform_id = d.pop("platformId", UNSET)
        platform_id: UUID | Unset
        if isinstance(_platform_id, Unset):
            platform_id = UNSET
        else:
            platform_id = UUID(_platform_id)

        restore_points_count = d.pop("restorePointsCount", UNSET)

        _vi_type = d.pop("viType", UNSET)
        vi_type: EVmwareInventoryType | Unset
        if isinstance(_vi_type, Unset):
            vi_type = UNSET
        else:
            vi_type = EVmwareInventoryType(_vi_type)

        path = d.pop("path", UNSET)

        vi_backup_object_model = cls(
            id=id,
            platform_name=platform_name,
            object_id=object_id,
            name=name,
            type_=type_,
            platform_id=platform_id,
            restore_points_count=restore_points_count,
            vi_type=vi_type,
            path=path,
        )

        vi_backup_object_model.additional_properties = d
        return vi_backup_object_model

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
