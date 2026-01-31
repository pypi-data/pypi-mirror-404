from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ip_settings_model import IpSettingsModel
    from ..models.linux_flr_helper_appliance_resource_model import LinuxFlrHelperApplianceResourceModel


T = TypeVar("T", bound="LinuxFlrHelperApplianceSpec")


@_attrs_define
class LinuxFlrHelperApplianceSpec:
    """Helper appliance settings. Use this option if you want to mount the file system to a temporary helper appliance.

    Attributes:
        platform_resource_settings (LinuxFlrHelperApplianceResourceModel | Unset): Helper appliance location.
        network_settings (IpSettingsModel | Unset): IP addressing settings for the helper appliance and DNS server.
        ftp_server_enabled (bool | Unset): If `true`, FTP access to the restored file system is enabled.
        restore_from_nss (bool | Unset): If `true`, the file system of the original machine is Novell Storage Services
            (NSS).
    """

    platform_resource_settings: LinuxFlrHelperApplianceResourceModel | Unset = UNSET
    network_settings: IpSettingsModel | Unset = UNSET
    ftp_server_enabled: bool | Unset = UNSET
    restore_from_nss: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform_resource_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.platform_resource_settings, Unset):
            platform_resource_settings = self.platform_resource_settings.to_dict()

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        ftp_server_enabled = self.ftp_server_enabled

        restore_from_nss = self.restore_from_nss

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if platform_resource_settings is not UNSET:
            field_dict["platformResourceSettings"] = platform_resource_settings
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings
        if ftp_server_enabled is not UNSET:
            field_dict["ftpServerEnabled"] = ftp_server_enabled
        if restore_from_nss is not UNSET:
            field_dict["restoreFromNSS"] = restore_from_nss

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ip_settings_model import IpSettingsModel
        from ..models.linux_flr_helper_appliance_resource_model import LinuxFlrHelperApplianceResourceModel

        d = dict(src_dict)
        _platform_resource_settings = d.pop("platformResourceSettings", UNSET)
        platform_resource_settings: LinuxFlrHelperApplianceResourceModel | Unset
        if isinstance(_platform_resource_settings, Unset):
            platform_resource_settings = UNSET
        else:
            platform_resource_settings = LinuxFlrHelperApplianceResourceModel.from_dict(_platform_resource_settings)

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: IpSettingsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = IpSettingsModel.from_dict(_network_settings)

        ftp_server_enabled = d.pop("ftpServerEnabled", UNSET)

        restore_from_nss = d.pop("restoreFromNSS", UNSET)

        linux_flr_helper_appliance_spec = cls(
            platform_resource_settings=platform_resource_settings,
            network_settings=network_settings,
            ftp_server_enabled=ftp_server_enabled,
            restore_from_nss=restore_from_nss,
        )

        linux_flr_helper_appliance_spec.additional_properties = d
        return linux_flr_helper_appliance_spec

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
