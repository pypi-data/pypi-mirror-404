from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_mount_mode_type import EFlrMountModeType
from ..models.e_flr_type import EFlrType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_auto_unmount_model import FlrAutoUnmountModel
    from ..models.linux_flr_mount_server_settings import LinuxFlrMountServerSettings


T = TypeVar("T", bound="LinuxFlrMountSpec")


@_attrs_define
class LinuxFlrMountSpec:
    """Restore settings for Linux file systems.

    Attributes:
        restore_point_id (UUID): ID of the restore point from which you want to restore files.
        type_ (EFlrType): Restore type.
        auto_unmount (FlrAutoUnmountModel): Settings for automatic unmount of the file system.
        mount_mode (EFlrMountModeType): Mount mode.
        reason (str | Unset): Reason for restoring files.
        mount_server (LinuxFlrMountServerSettings | Unset): Mount server settings for file restore from Linux machines.
            Specify these mount server settings if the `mountMode` property is set to `Manual`.
    """

    restore_point_id: UUID
    type_: EFlrType
    auto_unmount: FlrAutoUnmountModel
    mount_mode: EFlrMountModeType
    reason: str | Unset = UNSET
    mount_server: LinuxFlrMountServerSettings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        auto_unmount = self.auto_unmount.to_dict()

        mount_mode = self.mount_mode.value

        reason = self.reason

        mount_server: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mount_server, Unset):
            mount_server = self.mount_server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
                "autoUnmount": auto_unmount,
                "mountMode": mount_mode,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason
        if mount_server is not UNSET:
            field_dict["mountServer"] = mount_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_auto_unmount_model import FlrAutoUnmountModel
        from ..models.linux_flr_mount_server_settings import LinuxFlrMountServerSettings

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EFlrType(d.pop("type"))

        auto_unmount = FlrAutoUnmountModel.from_dict(d.pop("autoUnmount"))

        mount_mode = EFlrMountModeType(d.pop("mountMode"))

        reason = d.pop("reason", UNSET)

        _mount_server = d.pop("mountServer", UNSET)
        mount_server: LinuxFlrMountServerSettings | Unset
        if isinstance(_mount_server, Unset):
            mount_server = UNSET
        else:
            mount_server = LinuxFlrMountServerSettings.from_dict(_mount_server)

        linux_flr_mount_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            auto_unmount=auto_unmount,
            mount_mode=mount_mode,
            reason=reason,
            mount_server=mount_server,
        )

        linux_flr_mount_spec.additional_properties = d
        return linux_flr_mount_spec

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
