from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_throttling_target_type import EAgentThrottlingTargetType
from ..models.e_speed_unit import ESpeedUnit
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProtectionGroupAdvancedWindowsSettingsModel")


@_attrs_define
class ProtectionGroupAdvancedWindowsSettingsModel:
    """Advanced settings for Veeam Agent for Microsoft Windows machines.

    Attributes:
        throttling_enabled (bool | Unset): If `true`, bandwidth limit is enabled.
        throttling_unit (ESpeedUnit | Unset): Traffic speed unit.
        throttling_value (int | Unset): Bandwidth limit value.
        restrict_backup_over_metered_connection (bool | Unset): If `true`, backup over metered connections is disabled.
        restrict_backup_over_vpn_connection (bool | Unset): If `true`, backup over VPN connections is disabled.
        use_specified_wifi_networks (bool | Unset): If `true`, Veeam Backup & Replication will restrict the Wi-Fi usage
            to specified networks.
        wifi_networks (list[str] | Unset): An array of SSIDs of the allowed Wi-Fi networks.
        agent_throttling_enabled (bool | Unset): If `true`, agent throttling is enabled.
        agent_throttling_target (EAgentThrottlingTargetType | Unset): Agent throttling target type.
        flr_without_admin_account_enabled (bool | Unset): If `true`, file-level restore without administrative
            privileges is enabled.
    """

    throttling_enabled: bool | Unset = UNSET
    throttling_unit: ESpeedUnit | Unset = UNSET
    throttling_value: int | Unset = UNSET
    restrict_backup_over_metered_connection: bool | Unset = UNSET
    restrict_backup_over_vpn_connection: bool | Unset = UNSET
    use_specified_wifi_networks: bool | Unset = UNSET
    wifi_networks: list[str] | Unset = UNSET
    agent_throttling_enabled: bool | Unset = UNSET
    agent_throttling_target: EAgentThrottlingTargetType | Unset = UNSET
    flr_without_admin_account_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        throttling_enabled = self.throttling_enabled

        throttling_unit: str | Unset = UNSET
        if not isinstance(self.throttling_unit, Unset):
            throttling_unit = self.throttling_unit.value

        throttling_value = self.throttling_value

        restrict_backup_over_metered_connection = self.restrict_backup_over_metered_connection

        restrict_backup_over_vpn_connection = self.restrict_backup_over_vpn_connection

        use_specified_wifi_networks = self.use_specified_wifi_networks

        wifi_networks: list[str] | Unset = UNSET
        if not isinstance(self.wifi_networks, Unset):
            wifi_networks = self.wifi_networks

        agent_throttling_enabled = self.agent_throttling_enabled

        agent_throttling_target: str | Unset = UNSET
        if not isinstance(self.agent_throttling_target, Unset):
            agent_throttling_target = self.agent_throttling_target.value

        flr_without_admin_account_enabled = self.flr_without_admin_account_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if throttling_enabled is not UNSET:
            field_dict["throttlingEnabled"] = throttling_enabled
        if throttling_unit is not UNSET:
            field_dict["throttlingUnit"] = throttling_unit
        if throttling_value is not UNSET:
            field_dict["throttlingValue"] = throttling_value
        if restrict_backup_over_metered_connection is not UNSET:
            field_dict["restrictBackupOverMeteredConnection"] = restrict_backup_over_metered_connection
        if restrict_backup_over_vpn_connection is not UNSET:
            field_dict["restrictBackupOverVPNConnection"] = restrict_backup_over_vpn_connection
        if use_specified_wifi_networks is not UNSET:
            field_dict["useSpecifiedWifiNetworks"] = use_specified_wifi_networks
        if wifi_networks is not UNSET:
            field_dict["wifiNetworks"] = wifi_networks
        if agent_throttling_enabled is not UNSET:
            field_dict["agentThrottlingEnabled"] = agent_throttling_enabled
        if agent_throttling_target is not UNSET:
            field_dict["agentThrottlingTarget"] = agent_throttling_target
        if flr_without_admin_account_enabled is not UNSET:
            field_dict["FLRWithoutAdminAccountEnabled"] = flr_without_admin_account_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        throttling_enabled = d.pop("throttlingEnabled", UNSET)

        _throttling_unit = d.pop("throttlingUnit", UNSET)
        throttling_unit: ESpeedUnit | Unset
        if isinstance(_throttling_unit, Unset):
            throttling_unit = UNSET
        else:
            throttling_unit = ESpeedUnit(_throttling_unit)

        throttling_value = d.pop("throttlingValue", UNSET)

        restrict_backup_over_metered_connection = d.pop("restrictBackupOverMeteredConnection", UNSET)

        restrict_backup_over_vpn_connection = d.pop("restrictBackupOverVPNConnection", UNSET)

        use_specified_wifi_networks = d.pop("useSpecifiedWifiNetworks", UNSET)

        wifi_networks = cast(list[str], d.pop("wifiNetworks", UNSET))

        agent_throttling_enabled = d.pop("agentThrottlingEnabled", UNSET)

        _agent_throttling_target = d.pop("agentThrottlingTarget", UNSET)
        agent_throttling_target: EAgentThrottlingTargetType | Unset
        if isinstance(_agent_throttling_target, Unset):
            agent_throttling_target = UNSET
        else:
            agent_throttling_target = EAgentThrottlingTargetType(_agent_throttling_target)

        flr_without_admin_account_enabled = d.pop("FLRWithoutAdminAccountEnabled", UNSET)

        protection_group_advanced_windows_settings_model = cls(
            throttling_enabled=throttling_enabled,
            throttling_unit=throttling_unit,
            throttling_value=throttling_value,
            restrict_backup_over_metered_connection=restrict_backup_over_metered_connection,
            restrict_backup_over_vpn_connection=restrict_backup_over_vpn_connection,
            use_specified_wifi_networks=use_specified_wifi_networks,
            wifi_networks=wifi_networks,
            agent_throttling_enabled=agent_throttling_enabled,
            agent_throttling_target=agent_throttling_target,
            flr_without_admin_account_enabled=flr_without_admin_account_enabled,
        )

        protection_group_advanced_windows_settings_model.additional_properties = d
        return protection_group_advanced_windows_settings_model

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
