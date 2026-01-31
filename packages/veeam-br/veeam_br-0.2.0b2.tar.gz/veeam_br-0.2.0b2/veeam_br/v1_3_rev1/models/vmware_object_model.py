from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_inventory_platform_type import EInventoryPlatformType
from ..models.e_vmware_inventory_type import EVmwareInventoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.common_meta_info import CommonMetaInfo


T = TypeVar("T", bound="VmwareObjectModel")


@_attrs_define
class VmwareObjectModel:
    """VMware vSphere object.

    Attributes:
        platform (EInventoryPlatformType): Platform type of inventory object.
        host_name (str): Name of the VMware vSphere server that hosts the object.
        name (str): Name of the VMware vSphere object.
        type_ (EVmwareInventoryType): Type of the VMware vSphere object.<p> Note that inventory objects with multiple
            tags (*Multitag* type) can only be added in the Veeam Backup & Replication UI or PowerShell.
        size (str | Unset): Object size.
        object_id (str | Unset): ID of the VMware vSphere object. The parameter is required for all VMware vSphere
            objects except vCenter Servers and standalone ESXi hosts.
        urn (str | Unset): Uniform Resource Name (URN) of the object.
        is_enabled (bool | Unset): Indicates whether the VMware vSphere object is enabled or disabled.
        metadata (list[CommonMetaInfo] | Unset): Array of meta information about VMware vSphere object model.
    """

    platform: EInventoryPlatformType
    host_name: str
    name: str
    type_: EVmwareInventoryType
    size: str | Unset = UNSET
    object_id: str | Unset = UNSET
    urn: str | Unset = UNSET
    is_enabled: bool | Unset = UNSET
    metadata: list[CommonMetaInfo] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform.value

        host_name = self.host_name

        name = self.name

        type_ = self.type_.value

        size = self.size

        object_id = self.object_id

        urn = self.urn

        is_enabled = self.is_enabled

        metadata: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = []
            for metadata_item_data in self.metadata:
                metadata_item = metadata_item_data.to_dict()
                metadata.append(metadata_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "platform": platform,
                "hostName": host_name,
                "name": name,
                "type": type_,
            }
        )
        if size is not UNSET:
            field_dict["size"] = size
        if object_id is not UNSET:
            field_dict["objectId"] = object_id
        if urn is not UNSET:
            field_dict["urn"] = urn
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.common_meta_info import CommonMetaInfo

        d = dict(src_dict)
        platform = EInventoryPlatformType(d.pop("platform"))

        host_name = d.pop("hostName")

        name = d.pop("name")

        type_ = EVmwareInventoryType(d.pop("type"))

        size = d.pop("size", UNSET)

        object_id = d.pop("objectId", UNSET)

        urn = d.pop("urn", UNSET)

        is_enabled = d.pop("isEnabled", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: list[CommonMetaInfo] | Unset = UNSET
        if _metadata is not UNSET:
            metadata = []
            for metadata_item_data in _metadata:
                metadata_item = CommonMetaInfo.from_dict(metadata_item_data)

                metadata.append(metadata_item)

        vmware_object_model = cls(
            platform=platform,
            host_name=host_name,
            name=name,
            type_=type_,
            size=size,
            object_id=object_id,
            urn=urn,
            is_enabled=is_enabled,
            metadata=metadata,
        )

        vmware_object_model.additional_properties = d
        return vmware_object_model

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
