from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.v_power_nfs_port_settings_model import VPowerNFSPortSettingsModel


T = TypeVar("T", bound="MountServerSettingsModel")


@_attrs_define
class MountServerSettingsModel:
    """Settings for the mount server that is used for file and application items restore.

    Attributes:
        mount_server_id (UUID): ID of the mount server.
        write_cache_folder (str): Path to the folder used for writing cache during mount operations.
        v_power_nfs_enabled (bool): If `true`, the vPower NFS Service is enabled on the mount server.
        v_power_nfs_port_settings (VPowerNFSPortSettingsModel | Unset): Network ports used by the vPower NFS Service.
    """

    mount_server_id: UUID
    write_cache_folder: str
    v_power_nfs_enabled: bool
    v_power_nfs_port_settings: VPowerNFSPortSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mount_server_id = str(self.mount_server_id)

        write_cache_folder = self.write_cache_folder

        v_power_nfs_enabled = self.v_power_nfs_enabled

        v_power_nfs_port_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.v_power_nfs_port_settings, Unset):
            v_power_nfs_port_settings = self.v_power_nfs_port_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mountServerId": mount_server_id,
                "writeCacheFolder": write_cache_folder,
                "vPowerNFSEnabled": v_power_nfs_enabled,
            }
        )
        if v_power_nfs_port_settings is not UNSET:
            field_dict["vPowerNFSPortSettings"] = v_power_nfs_port_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v_power_nfs_port_settings_model import VPowerNFSPortSettingsModel

        d = dict(src_dict)
        mount_server_id = UUID(d.pop("mountServerId"))

        write_cache_folder = d.pop("writeCacheFolder")

        v_power_nfs_enabled = d.pop("vPowerNFSEnabled")

        _v_power_nfs_port_settings = d.pop("vPowerNFSPortSettings", UNSET)
        v_power_nfs_port_settings: VPowerNFSPortSettingsModel | Unset
        if isinstance(_v_power_nfs_port_settings, Unset):
            v_power_nfs_port_settings = UNSET
        else:
            v_power_nfs_port_settings = VPowerNFSPortSettingsModel.from_dict(_v_power_nfs_port_settings)

        mount_server_settings_model = cls(
            mount_server_id=mount_server_id,
            write_cache_folder=write_cache_folder,
            v_power_nfs_enabled=v_power_nfs_enabled,
            v_power_nfs_port_settings=v_power_nfs_port_settings,
        )

        mount_server_settings_model.additional_properties = d
        return mount_server_settings_model

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
