from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel
    from ..models.wan_accelerator_settings_model import WanAcceleratorSettingsModel


T = TypeVar("T", bound="VSphereReplicaJobDataTransferModel")


@_attrs_define
class VSphereReplicaJobDataTransferModel:
    """Data transfer settings.

    Attributes:
        source_proxies (BackupProxiesSettingsModel): Backup proxy settings.
        target_proxies (BackupProxiesSettingsModel): Backup proxy settings.
        wan_accelerator_settings (WanAcceleratorSettingsModel | Unset): WAN accelerator settings.
    """

    source_proxies: BackupProxiesSettingsModel
    target_proxies: BackupProxiesSettingsModel
    wan_accelerator_settings: WanAcceleratorSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_proxies = self.source_proxies.to_dict()

        target_proxies = self.target_proxies.to_dict()

        wan_accelerator_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.wan_accelerator_settings, Unset):
            wan_accelerator_settings = self.wan_accelerator_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourceProxies": source_proxies,
                "targetProxies": target_proxies,
            }
        )
        if wan_accelerator_settings is not UNSET:
            field_dict["wanAcceleratorSettings"] = wan_accelerator_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_proxies_settings_model import BackupProxiesSettingsModel
        from ..models.wan_accelerator_settings_model import WanAcceleratorSettingsModel

        d = dict(src_dict)
        source_proxies = BackupProxiesSettingsModel.from_dict(d.pop("sourceProxies"))

        target_proxies = BackupProxiesSettingsModel.from_dict(d.pop("targetProxies"))

        _wan_accelerator_settings = d.pop("wanAcceleratorSettings", UNSET)
        wan_accelerator_settings: WanAcceleratorSettingsModel | Unset
        if isinstance(_wan_accelerator_settings, Unset):
            wan_accelerator_settings = UNSET
        else:
            wan_accelerator_settings = WanAcceleratorSettingsModel.from_dict(_wan_accelerator_settings)

        v_sphere_replica_job_data_transfer_model = cls(
            source_proxies=source_proxies,
            target_proxies=target_proxies,
            wan_accelerator_settings=wan_accelerator_settings,
        )

        v_sphere_replica_job_data_transfer_model.additional_properties = d
        return v_sphere_replica_job_data_transfer_model

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
