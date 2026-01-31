from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.pre_installed_agents_protection_group_package_spec_format import (
    PreInstalledAgentsProtectionGroupPackageSpecFormat,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pre_installed_agents_packages_model import PreInstalledAgentsPackagesModel


T = TypeVar("T", bound="PreInstalledAgentsProtectionGroupPackageSpec")


@_attrs_define
class PreInstalledAgentsProtectionGroupPackageSpec:
    """Package download settings.

    Attributes:
        format_ (PreInstalledAgentsProtectionGroupPackageSpecFormat | Unset): Format of the Veeam Agent package.
        include_windows_packages (bool | Unset): If `true`, Microsoft Windows packages will be downloaded.
        include_mac_packages (bool | Unset): If `true`, Mac packages will be downloaded.
        linux_packages (PreInstalledAgentsPackagesModel | Unset): Pre-installed packages on the protection group.
        unix_packages (PreInstalledAgentsPackagesModel | Unset): Pre-installed packages on the protection group.
    """

    format_: PreInstalledAgentsProtectionGroupPackageSpecFormat | Unset = UNSET
    include_windows_packages: bool | Unset = UNSET
    include_mac_packages: bool | Unset = UNSET
    linux_packages: PreInstalledAgentsPackagesModel | Unset = UNSET
    unix_packages: PreInstalledAgentsPackagesModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        format_: str | Unset = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        include_windows_packages = self.include_windows_packages

        include_mac_packages = self.include_mac_packages

        linux_packages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux_packages, Unset):
            linux_packages = self.linux_packages.to_dict()

        unix_packages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.unix_packages, Unset):
            unix_packages = self.unix_packages.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if format_ is not UNSET:
            field_dict["format"] = format_
        if include_windows_packages is not UNSET:
            field_dict["includeWindowsPackages"] = include_windows_packages
        if include_mac_packages is not UNSET:
            field_dict["includeMacPackages"] = include_mac_packages
        if linux_packages is not UNSET:
            field_dict["linuxPackages"] = linux_packages
        if unix_packages is not UNSET:
            field_dict["unixPackages"] = unix_packages

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pre_installed_agents_packages_model import PreInstalledAgentsPackagesModel

        d = dict(src_dict)
        _format_ = d.pop("format", UNSET)
        format_: PreInstalledAgentsProtectionGroupPackageSpecFormat | Unset
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = PreInstalledAgentsProtectionGroupPackageSpecFormat(_format_)

        include_windows_packages = d.pop("includeWindowsPackages", UNSET)

        include_mac_packages = d.pop("includeMacPackages", UNSET)

        _linux_packages = d.pop("linuxPackages", UNSET)
        linux_packages: PreInstalledAgentsPackagesModel | Unset
        if isinstance(_linux_packages, Unset):
            linux_packages = UNSET
        else:
            linux_packages = PreInstalledAgentsPackagesModel.from_dict(_linux_packages)

        _unix_packages = d.pop("unixPackages", UNSET)
        unix_packages: PreInstalledAgentsPackagesModel | Unset
        if isinstance(_unix_packages, Unset):
            unix_packages = UNSET
        else:
            unix_packages = PreInstalledAgentsPackagesModel.from_dict(_unix_packages)

        pre_installed_agents_protection_group_package_spec = cls(
            format_=format_,
            include_windows_packages=include_windows_packages,
            include_mac_packages=include_mac_packages,
            linux_packages=linux_packages,
            unix_packages=unix_packages,
        )

        pre_installed_agents_protection_group_package_spec.additional_properties = d
        return pre_installed_agents_protection_group_package_spec

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
