from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_auto_unmount_model import FlrAutoUnmountModel


T = TypeVar("T", bound="UnstructuredDataMountSpec")


@_attrs_define
class UnstructuredDataMountSpec:
    """
    Attributes:
        backup_id (UUID): Backup ID.
        auto_unmount (FlrAutoUnmountModel | Unset): Settings for automatic unmount of the file system.
    """

    backup_id: UUID
    auto_unmount: FlrAutoUnmountModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_id = str(self.backup_id)

        auto_unmount: dict[str, Any] | Unset = UNSET
        if not isinstance(self.auto_unmount, Unset):
            auto_unmount = self.auto_unmount.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupId": backup_id,
            }
        )
        if auto_unmount is not UNSET:
            field_dict["autoUnmount"] = auto_unmount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_auto_unmount_model import FlrAutoUnmountModel

        d = dict(src_dict)
        backup_id = UUID(d.pop("backupId"))

        _auto_unmount = d.pop("autoUnmount", UNSET)
        auto_unmount: FlrAutoUnmountModel | Unset
        if isinstance(_auto_unmount, Unset):
            auto_unmount = UNSET
        else:
            auto_unmount = FlrAutoUnmountModel.from_dict(_auto_unmount)

        unstructured_data_mount_spec = cls(
            backup_id=backup_id,
            auto_unmount=auto_unmount,
        )

        unstructured_data_mount_spec.additional_properties = d
        return unstructured_data_mount_spec

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
