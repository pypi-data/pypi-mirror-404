from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_host_import_spec import CloudDirectorHostImportSpec
    from ..models.linux_host_import_spec import LinuxHostImportSpec
    from ..models.vi_host_import_spec import ViHostImportSpec
    from ..models.windows_host_import_spec import WindowsHostImportSpec


T = TypeVar("T", bound="ManageServerImportSpecCollection")


@_attrs_define
class ManageServerImportSpecCollection:
    """
    Attributes:
        windows_hosts (list[WindowsHostImportSpec] | Unset): Array of managed Microsoft Windows servers.
        linux_hosts (list[LinuxHostImportSpec] | Unset): Array of managed Linux servers.
        vi_hosts (list[ViHostImportSpec] | Unset): Array of VMware vSphere servers.
        cloud_director_hosts (list[CloudDirectorHostImportSpec] | Unset): Array of VMware Cloud Director servers.
    """

    windows_hosts: list[WindowsHostImportSpec] | Unset = UNSET
    linux_hosts: list[LinuxHostImportSpec] | Unset = UNSET
    vi_hosts: list[ViHostImportSpec] | Unset = UNSET
    cloud_director_hosts: list[CloudDirectorHostImportSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        windows_hosts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.windows_hosts, Unset):
            windows_hosts = []
            for windows_hosts_item_data in self.windows_hosts:
                windows_hosts_item = windows_hosts_item_data.to_dict()
                windows_hosts.append(windows_hosts_item)

        linux_hosts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.linux_hosts, Unset):
            linux_hosts = []
            for linux_hosts_item_data in self.linux_hosts:
                linux_hosts_item = linux_hosts_item_data.to_dict()
                linux_hosts.append(linux_hosts_item)

        vi_hosts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.vi_hosts, Unset):
            vi_hosts = []
            for vi_hosts_item_data in self.vi_hosts:
                vi_hosts_item = vi_hosts_item_data.to_dict()
                vi_hosts.append(vi_hosts_item)

        cloud_director_hosts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.cloud_director_hosts, Unset):
            cloud_director_hosts = []
            for cloud_director_hosts_item_data in self.cloud_director_hosts:
                cloud_director_hosts_item = cloud_director_hosts_item_data.to_dict()
                cloud_director_hosts.append(cloud_director_hosts_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if windows_hosts is not UNSET:
            field_dict["windowsHosts"] = windows_hosts
        if linux_hosts is not UNSET:
            field_dict["linuxHosts"] = linux_hosts
        if vi_hosts is not UNSET:
            field_dict["viHosts"] = vi_hosts
        if cloud_director_hosts is not UNSET:
            field_dict["cloudDirectorHosts"] = cloud_director_hosts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_host_import_spec import CloudDirectorHostImportSpec
        from ..models.linux_host_import_spec import LinuxHostImportSpec
        from ..models.vi_host_import_spec import ViHostImportSpec
        from ..models.windows_host_import_spec import WindowsHostImportSpec

        d = dict(src_dict)
        _windows_hosts = d.pop("windowsHosts", UNSET)
        windows_hosts: list[WindowsHostImportSpec] | Unset = UNSET
        if _windows_hosts is not UNSET:
            windows_hosts = []
            for windows_hosts_item_data in _windows_hosts:
                windows_hosts_item = WindowsHostImportSpec.from_dict(windows_hosts_item_data)

                windows_hosts.append(windows_hosts_item)

        _linux_hosts = d.pop("linuxHosts", UNSET)
        linux_hosts: list[LinuxHostImportSpec] | Unset = UNSET
        if _linux_hosts is not UNSET:
            linux_hosts = []
            for linux_hosts_item_data in _linux_hosts:
                linux_hosts_item = LinuxHostImportSpec.from_dict(linux_hosts_item_data)

                linux_hosts.append(linux_hosts_item)

        _vi_hosts = d.pop("viHosts", UNSET)
        vi_hosts: list[ViHostImportSpec] | Unset = UNSET
        if _vi_hosts is not UNSET:
            vi_hosts = []
            for vi_hosts_item_data in _vi_hosts:
                vi_hosts_item = ViHostImportSpec.from_dict(vi_hosts_item_data)

                vi_hosts.append(vi_hosts_item)

        _cloud_director_hosts = d.pop("cloudDirectorHosts", UNSET)
        cloud_director_hosts: list[CloudDirectorHostImportSpec] | Unset = UNSET
        if _cloud_director_hosts is not UNSET:
            cloud_director_hosts = []
            for cloud_director_hosts_item_data in _cloud_director_hosts:
                cloud_director_hosts_item = CloudDirectorHostImportSpec.from_dict(cloud_director_hosts_item_data)

                cloud_director_hosts.append(cloud_director_hosts_item)

        manage_server_import_spec_collection = cls(
            windows_hosts=windows_hosts,
            linux_hosts=linux_hosts,
            vi_hosts=vi_hosts,
            cloud_director_hosts=cloud_director_hosts,
        )

        manage_server_import_spec_collection.additional_properties = d
        return manage_server_import_spec_collection

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
