from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_hype_v_proxy_type import EHypeVProxyType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.off_host_backup_proxy_model import OffHostBackupProxyModel


T = TypeVar("T", bound="HyperVBackupProxiesSettingsModel")


@_attrs_define
class HyperVBackupProxiesSettingsModel:
    """Microsoft Hyper-V backup proxy settings.

    Attributes:
        proxy_type (EHypeVProxyType): Microsoft Hyper-V backup proxy mode.
        off_host_settings (OffHostBackupProxyModel | Unset): Off-host backup proxy settings.
    """

    proxy_type: EHypeVProxyType
    off_host_settings: OffHostBackupProxyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        proxy_type = self.proxy_type.value

        off_host_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.off_host_settings, Unset):
            off_host_settings = self.off_host_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "proxyType": proxy_type,
            }
        )
        if off_host_settings is not UNSET:
            field_dict["offHostSettings"] = off_host_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.off_host_backup_proxy_model import OffHostBackupProxyModel

        d = dict(src_dict)
        proxy_type = EHypeVProxyType(d.pop("proxyType"))

        _off_host_settings = d.pop("offHostSettings", UNSET)
        off_host_settings: OffHostBackupProxyModel | Unset
        if isinstance(_off_host_settings, Unset):
            off_host_settings = UNSET
        else:
            off_host_settings = OffHostBackupProxyModel.from_dict(_off_host_settings)

        hyper_v_backup_proxies_settings_model = cls(
            proxy_type=proxy_type,
            off_host_settings=off_host_settings,
        )

        hyper_v_backup_proxies_settings_model.additional_properties = d
        return hyper_v_backup_proxies_settings_model

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
