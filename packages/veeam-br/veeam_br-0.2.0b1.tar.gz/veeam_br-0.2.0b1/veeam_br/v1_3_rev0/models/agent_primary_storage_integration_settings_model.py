from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel


T = TypeVar("T", bound="AgentPrimaryStorageIntegrationSettingsModel")


@_attrs_define
class AgentPrimaryStorageIntegrationSettingsModel:
    """Settings for primary storage integration.

    Attributes:
        is_enabled (bool): If `true`, the primary storage integration is enabled. In this case, storage snapshots
            (instead of VM snapshots) are used for VM data processing.
        off_host_backup_proxies (BackupProxiesSettingsModel | Unset): VMware vSphere backup proxy settings.
        failover_to_on_host_agent (bool | Unset): If `true`, Veeam Backup & Replication fails over to a backup operation
            with a software VSS provider.
    """

    is_enabled: bool
    off_host_backup_proxies: BackupProxiesSettingsModel | Unset = UNSET
    failover_to_on_host_agent: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        off_host_backup_proxies: dict[str, Any] | Unset = UNSET
        if not isinstance(self.off_host_backup_proxies, Unset):
            off_host_backup_proxies = self.off_host_backup_proxies.to_dict()

        failover_to_on_host_agent = self.failover_to_on_host_agent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if off_host_backup_proxies is not UNSET:
            field_dict["offHostBackupProxies"] = off_host_backup_proxies
        if failover_to_on_host_agent is not UNSET:
            field_dict["failoverToOnHostAgent"] = failover_to_on_host_agent

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _off_host_backup_proxies = d.pop("offHostBackupProxies", UNSET)
        off_host_backup_proxies: BackupProxiesSettingsModel | Unset
        if isinstance(_off_host_backup_proxies, Unset):
            off_host_backup_proxies = UNSET
        else:
            off_host_backup_proxies = BackupProxiesSettingsModel.from_dict(_off_host_backup_proxies)

        failover_to_on_host_agent = d.pop("failoverToOnHostAgent", UNSET)

        agent_primary_storage_integration_settings_model = cls(
            is_enabled=is_enabled,
            off_host_backup_proxies=off_host_backup_proxies,
            failover_to_on_host_agent=failover_to_on_host_agent,
        )

        agent_primary_storage_integration_settings_model.additional_properties = d
        return agent_primary_storage_integration_settings_model

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
