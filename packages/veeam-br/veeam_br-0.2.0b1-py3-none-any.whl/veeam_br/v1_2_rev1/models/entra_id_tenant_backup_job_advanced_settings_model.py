from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
    from ..models.entra_id_tenant_notification_settings_model import EntraIDTenantNotificationSettingsModel


T = TypeVar("T", bound="EntraIDTenantBackupJobAdvancedSettingsModel")


@_attrs_define
class EntraIDTenantBackupJobAdvancedSettingsModel:
    """Advanced job settings.

    Attributes:
        notifications (EntraIDTenantNotificationSettingsModel | Unset): Notification settings.
        encryption (BackupStorageSettingsEncryptionModel | Unset): Encryption of backup files.
    """

    notifications: EntraIDTenantNotificationSettingsModel | Unset = UNSET
    encryption: BackupStorageSettingsEncryptionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        encryption: dict[str, Any] | Unset = UNSET
        if not isinstance(self.encryption, Unset):
            encryption = self.encryption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if encryption is not UNSET:
            field_dict["encryption"] = encryption

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
        from ..models.entra_id_tenant_notification_settings_model import EntraIDTenantNotificationSettingsModel

        d = dict(src_dict)
        _notifications = d.pop("notifications", UNSET)
        notifications: EntraIDTenantNotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = EntraIDTenantNotificationSettingsModel.from_dict(_notifications)

        _encryption = d.pop("encryption", UNSET)
        encryption: BackupStorageSettingsEncryptionModel | Unset
        if isinstance(_encryption, Unset):
            encryption = UNSET
        else:
            encryption = BackupStorageSettingsEncryptionModel.from_dict(_encryption)

        entra_id_tenant_backup_job_advanced_settings_model = cls(
            notifications=notifications,
            encryption=encryption,
        )

        entra_id_tenant_backup_job_advanced_settings_model.additional_properties = d
        return entra_id_tenant_backup_job_advanced_settings_model

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
