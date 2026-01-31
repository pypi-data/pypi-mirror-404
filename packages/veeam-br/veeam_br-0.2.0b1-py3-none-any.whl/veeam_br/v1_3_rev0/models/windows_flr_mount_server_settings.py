from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_mount_mode_server_type import EFlrMountModeServerType

T = TypeVar("T", bound="WindowsFlrMountServerSettings")


@_attrs_define
class WindowsFlrMountServerSettings:
    """Mount server settings for file restore from Windows machines. Specify these mount server settings if the `mountMode`
    property is set to `Manual`.

        Attributes:
            mount_server_type (EFlrMountModeServerType): Mount server mode.
            mount_server_id (UUID): Mount server ID. Specify this property if the `mountServerType` property is
                `MountServer`.
    """

    mount_server_type: EFlrMountModeServerType
    mount_server_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mount_server_type = self.mount_server_type.value

        mount_server_id = str(self.mount_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mountServerType": mount_server_type,
                "mountServerId": mount_server_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mount_server_type = EFlrMountModeServerType(d.pop("mountServerType"))

        mount_server_id = UUID(d.pop("mountServerId"))

        windows_flr_mount_server_settings = cls(
            mount_server_type=mount_server_type,
            mount_server_id=mount_server_id,
        )

        windows_flr_mount_server_settings.additional_properties = d
        return windows_flr_mount_server_settings

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
