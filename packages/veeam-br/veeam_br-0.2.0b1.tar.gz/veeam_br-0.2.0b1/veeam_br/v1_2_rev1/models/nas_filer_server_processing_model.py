from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_io_control_level import EBackupIOControlLevel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel


T = TypeVar("T", bound="NASFilerServerProcessingModel")


@_attrs_define
class NASFilerServerProcessingModel:
    """
    Attributes:
        backup_proxies (BackupProxiesSettingsModel): Backup proxy settings.
        cache_repository_id (UUID): ID of a backup repository that is used as a cache repository for the tenant.
        backup_io_control_level (EBackupIOControlLevel | Unset):
        native_change_tracking_enabled (bool | Unset):
    """

    backup_proxies: BackupProxiesSettingsModel
    cache_repository_id: UUID
    backup_io_control_level: EBackupIOControlLevel | Unset = UNSET
    native_change_tracking_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_proxies = self.backup_proxies.to_dict()

        cache_repository_id = str(self.cache_repository_id)

        backup_io_control_level: str | Unset = UNSET
        if not isinstance(self.backup_io_control_level, Unset):
            backup_io_control_level = self.backup_io_control_level.value

        native_change_tracking_enabled = self.native_change_tracking_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupProxies": backup_proxies,
                "cacheRepositoryId": cache_repository_id,
            }
        )
        if backup_io_control_level is not UNSET:
            field_dict["backupIOControlLevel"] = backup_io_control_level
        if native_change_tracking_enabled is not UNSET:
            field_dict["nativeChangeTrackingEnabled"] = native_change_tracking_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel

        d = dict(src_dict)
        backup_proxies = BackupProxiesSettingsModel.from_dict(d.pop("backupProxies"))

        cache_repository_id = UUID(d.pop("cacheRepositoryId"))

        _backup_io_control_level = d.pop("backupIOControlLevel", UNSET)
        backup_io_control_level: EBackupIOControlLevel | Unset
        if isinstance(_backup_io_control_level, Unset):
            backup_io_control_level = UNSET
        else:
            backup_io_control_level = EBackupIOControlLevel(_backup_io_control_level)

        native_change_tracking_enabled = d.pop("nativeChangeTrackingEnabled", UNSET)

        nas_filer_server_processing_model = cls(
            backup_proxies=backup_proxies,
            cache_repository_id=cache_repository_id,
            backup_io_control_level=backup_io_control_level,
            native_change_tracking_enabled=native_change_tracking_enabled,
        )

        nas_filer_server_processing_model.additional_properties = d
        return nas_filer_server_processing_model

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
