from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_mount_mode_server_type import EFlrMountModeServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_flr_helper_appliance_spec import LinuxFlrHelperApplianceSpec
    from ..models.linux_flr_helper_host_model import LinuxFlrHelperHostModel
    from ..models.linux_flr_original_host_spec import LinuxFlrOriginalHostSpec


T = TypeVar("T", bound="LinuxFlrMountServerSettings")


@_attrs_define
class LinuxFlrMountServerSettings:
    """Mount server settings for file restore from Linux machines. Specify these mount server settings if the `mountMode`
    property is set to `Manual`.

        Attributes:
            mount_server_type (EFlrMountModeServerType): Mount server mode.
            mount_server_id (UUID | Unset): Mount server ID. Specify this property if the `mountServerType` property is
                `MountServer`.
            helper_host (LinuxFlrHelperHostModel | Unset): Helper host settings. Use this option if you want to mount the
                file system to a Linux server added to the backup infrastructure.
            helper_appliance (LinuxFlrHelperApplianceSpec | Unset): Helper appliance settings. Use this option if you want
                to mount the file system to a temporary helper appliance.
            original_host (LinuxFlrOriginalHostSpec | Unset): Original host settings. Use this option if you want to mount
                the file system to the original machine.
    """

    mount_server_type: EFlrMountModeServerType
    mount_server_id: UUID | Unset = UNSET
    helper_host: LinuxFlrHelperHostModel | Unset = UNSET
    helper_appliance: LinuxFlrHelperApplianceSpec | Unset = UNSET
    original_host: LinuxFlrOriginalHostSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mount_server_type = self.mount_server_type.value

        mount_server_id: str | Unset = UNSET
        if not isinstance(self.mount_server_id, Unset):
            mount_server_id = str(self.mount_server_id)

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
                "mountServerType": mount_server_type,
            }
        )
        if mount_server_id is not UNSET:
            field_dict["mountServerId"] = mount_server_id
        if helper_host is not UNSET:
            field_dict["helperHost"] = helper_host
        if helper_appliance is not UNSET:
            field_dict["helperAppliance"] = helper_appliance
        if original_host is not UNSET:
            field_dict["originalHost"] = original_host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_flr_helper_appliance_spec import LinuxFlrHelperApplianceSpec
        from ..models.linux_flr_helper_host_model import LinuxFlrHelperHostModel
        from ..models.linux_flr_original_host_spec import LinuxFlrOriginalHostSpec

        d = dict(src_dict)
        mount_server_type = EFlrMountModeServerType(d.pop("mountServerType"))

        _mount_server_id = d.pop("mountServerId", UNSET)
        mount_server_id: UUID | Unset
        if isinstance(_mount_server_id, Unset):
            mount_server_id = UNSET
        else:
            mount_server_id = UUID(_mount_server_id)

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

        linux_flr_mount_server_settings = cls(
            mount_server_type=mount_server_type,
            mount_server_id=mount_server_id,
            helper_host=helper_host,
            helper_appliance=helper_appliance,
            original_host=original_host,
        )

        linux_flr_mount_server_settings.additional_properties = d
        return linux_flr_mount_server_settings

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
