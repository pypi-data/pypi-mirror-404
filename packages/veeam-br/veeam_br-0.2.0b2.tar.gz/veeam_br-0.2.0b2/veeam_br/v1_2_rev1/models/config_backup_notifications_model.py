from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.config_backup_smtp_settigs_model import ConfigBackupSMTPSettigsModel


T = TypeVar("T", bound="ConfigBackupNotificationsModel")


@_attrs_define
class ConfigBackupNotificationsModel:
    """Notification settings.

    Attributes:
        snmp_enabled (bool): If `true`, SNMP traps are enabled for this job.
        smtp_settings (ConfigBackupSMTPSettigsModel | Unset): Email notification settings.
    """

    snmp_enabled: bool
    smtp_settings: ConfigBackupSMTPSettigsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        snmp_enabled = self.snmp_enabled

        smtp_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.smtp_settings, Unset):
            smtp_settings = self.smtp_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "SNMPEnabled": snmp_enabled,
            }
        )
        if smtp_settings is not UNSET:
            field_dict["SMTPSettings"] = smtp_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.config_backup_smtp_settigs_model import ConfigBackupSMTPSettigsModel

        d = dict(src_dict)
        snmp_enabled = d.pop("SNMPEnabled")

        _smtp_settings = d.pop("SMTPSettings", UNSET)
        smtp_settings: ConfigBackupSMTPSettigsModel | Unset
        if isinstance(_smtp_settings, Unset):
            smtp_settings = UNSET
        else:
            smtp_settings = ConfigBackupSMTPSettigsModel.from_dict(_smtp_settings)

        config_backup_notifications_model = cls(
            snmp_enabled=snmp_enabled,
            smtp_settings=smtp_settings,
        )

        config_backup_notifications_model.additional_properties = d
        return config_backup_notifications_model

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
