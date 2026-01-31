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
    from ..models.linux_flr_helper_appliance_spec import LinuxFlrHelperApplianceSpec
    from ..models.linux_flr_helper_host_model import LinuxFlrHelperHostModel
    from ..models.linux_flr_original_host_spec import LinuxFlrOriginalHostSpec


T = TypeVar("T", bound="LinuxFlrMountSpec")


@_attrs_define
class LinuxFlrMountSpec:
    """Restore settings for Linux file systems.

    Attributes:
        restore_point_id (UUID): ID of the restore point that you want to restore files from.
        type_ (EFlrType): Restore type.
        auto_unmount (FlrAutoUnmountModel): Settings for automatic unmount of the file system.
        reason (str | Unset): Reason for restoring files.
        helper_host (LinuxFlrHelperHostModel | Unset): Helper host settings. Use this option if you want to mount the
            file system to a Linux server added to the backup infrastructure.
        helper_appliance (LinuxFlrHelperApplianceSpec | Unset): Helper appliance settings. Use this option if you want
            to mount the file system to a temporary helper appliance.
        original_host (LinuxFlrOriginalHostSpec | Unset): Original host settings. Use this option if you want to mount
            the file system to the original machine.
    """

    restore_point_id: UUID
    type_: EFlrType
    auto_unmount: FlrAutoUnmountModel
    reason: str | Unset = UNSET
    helper_host: LinuxFlrHelperHostModel | Unset = UNSET
    helper_appliance: LinuxFlrHelperApplianceSpec | Unset = UNSET
    original_host: LinuxFlrOriginalHostSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        auto_unmount = self.auto_unmount.to_dict()

        reason = self.reason

        helper_host: dict[str, Any] | Unset = UNSET
        if not isinstance(self.helper_host, Unset):
            helper_host = self.helper_host.to_dict()

        helper_appliance: dict[str, Any] | Unset = UNSET
        if not isinstance(self.helper_appliance, Unset):
            helper_appliance = self.helper_appliance.to_dict()

        original_host: dict[str, Any] | Unset = UNSET
        if not isinstance(self.original_host, Unset):
            original_host = self.original_host.to_dict()

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
        if helper_host is not UNSET:
            field_dict["helperHost"] = helper_host
        if helper_appliance is not UNSET:
            field_dict["helperAppliance"] = helper_appliance
        if original_host is not UNSET:
            field_dict["originalHost"] = original_host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_auto_unmount_model import FlrAutoUnmountModel
        from ..models.linux_flr_helper_appliance_spec import LinuxFlrHelperApplianceSpec
        from ..models.linux_flr_helper_host_model import LinuxFlrHelperHostModel
        from ..models.linux_flr_original_host_spec import LinuxFlrOriginalHostSpec

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EFlrType(d.pop("type"))

        auto_unmount = FlrAutoUnmountModel.from_dict(d.pop("autoUnmount"))

        reason = d.pop("reason", UNSET)

        _helper_host = d.pop("helperHost", UNSET)
        helper_host: LinuxFlrHelperHostModel | Unset
        if isinstance(_helper_host, Unset):
            helper_host = UNSET
        else:
            helper_host = LinuxFlrHelperHostModel.from_dict(_helper_host)

        _helper_appliance = d.pop("helperAppliance", UNSET)
        helper_appliance: LinuxFlrHelperApplianceSpec | Unset
        if isinstance(_helper_appliance, Unset):
            helper_appliance = UNSET
        else:
            helper_appliance = LinuxFlrHelperApplianceSpec.from_dict(_helper_appliance)

        _original_host = d.pop("originalHost", UNSET)
        original_host: LinuxFlrOriginalHostSpec | Unset
        if isinstance(_original_host, Unset):
            original_host = UNSET
        else:
            original_host = LinuxFlrOriginalHostSpec.from_dict(_original_host)

        linux_flr_mount_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            auto_unmount=auto_unmount,
            reason=reason,
            helper_host=helper_host,
            helper_appliance=helper_appliance,
            original_host=original_host,
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
