from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_type import EFlrType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_auto_unmount_model import FlrAutoUnmountModel


T = TypeVar("T", bound="FlrMountSpec")


@_attrs_define
class FlrMountSpec:
    """File restore settings.

    Attributes:
        restore_point_id (UUID): ID of the restore point from which you want to restore files.
        type_ (EFlrType): Restore type.
        auto_unmount (FlrAutoUnmountModel): Settings for automatic unmount of the file system.
        reason (str | Unset): Reason for restoring files.
    """

    restore_point_id: UUID
    type_: EFlrType
    auto_unmount: FlrAutoUnmountModel
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        auto_unmount = self.auto_unmount.to_dict()

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
                "autoUnmount": auto_unmount,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_auto_unmount_model import FlrAutoUnmountModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EFlrType(d.pop("type"))

        auto_unmount = FlrAutoUnmountModel.from_dict(d.pop("autoUnmount"))

        reason = d.pop("reason", UNSET)

        flr_mount_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            auto_unmount=auto_unmount,
            reason=reason,
        )

        flr_mount_spec.additional_properties = d
        return flr_mount_spec

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
