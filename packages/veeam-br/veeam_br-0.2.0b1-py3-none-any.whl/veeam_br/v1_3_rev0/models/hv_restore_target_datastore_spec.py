from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hyper_v_disk_extent_model import HyperVDiskExtentModel


T = TypeVar("T", bound="HvRestoreTargetDatastoreSpec")


@_attrs_define
class HvRestoreTargetDatastoreSpec:
    """Destination datastore.

    Attributes:
        disk (HyperVDiskExtentModel): Disk extent of Hyper-V host.
        target_folder (str): Absolute path to the folder, where the disk should be placed in the target datastore.
    """

    disk: HyperVDiskExtentModel
    target_folder: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disk = self.disk.to_dict()

        target_folder = self.target_folder

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "disk": disk,
                "targetFolder": target_folder,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_disk_extent_model import HyperVDiskExtentModel

        d = dict(src_dict)
        disk = HyperVDiskExtentModel.from_dict(d.pop("disk"))

        target_folder = d.pop("targetFolder")

        hv_restore_target_datastore_spec = cls(
            disk=disk,
            target_folder=target_folder,
        )

        hv_restore_target_datastore_spec.additional_properties = d
        return hv_restore_target_datastore_spec

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
