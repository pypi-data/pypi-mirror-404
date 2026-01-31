from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_instant_vm_recovery_switchover_settings_model import (
        AzureInstantVMRecoverySwitchoverSettingsModel,
    )


T = TypeVar("T", bound="AzureInstantVMRecoveryMigrationSpec")


@_attrs_define
class AzureInstantVMRecoveryMigrationSpec:
    """Migration settings.

    Attributes:
        switchover_settings (AzureInstantVMRecoverySwitchoverSettingsModel | Unset): Switchover settings for Instant
            Recovery to Azure.
    """

    switchover_settings: AzureInstantVMRecoverySwitchoverSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        switchover_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.switchover_settings, Unset):
            switchover_settings = self.switchover_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if switchover_settings is not UNSET:
            field_dict["switchoverSettings"] = switchover_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_instant_vm_recovery_switchover_settings_model import (
            AzureInstantVMRecoverySwitchoverSettingsModel,
        )

        d = dict(src_dict)
        _switchover_settings = d.pop("switchoverSettings", UNSET)
        switchover_settings: AzureInstantVMRecoverySwitchoverSettingsModel | Unset
        if isinstance(_switchover_settings, Unset):
            switchover_settings = UNSET
        else:
            switchover_settings = AzureInstantVMRecoverySwitchoverSettingsModel.from_dict(_switchover_settings)

        azure_instant_vm_recovery_migration_spec = cls(
            switchover_settings=switchover_settings,
        )

        azure_instant_vm_recovery_migration_spec.additional_properties = d
        return azure_instant_vm_recovery_migration_spec

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
