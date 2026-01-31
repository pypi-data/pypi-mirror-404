from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupProxiesSettingsModel")


@_attrs_define
class BackupProxiesSettingsModel:
    """Backup proxy settings.

    Attributes:
        auto_select_enabled (bool): If `true`, backup proxies are detected and assigned automatically. Default: True.
        proxy_ids (list[UUID] | Unset): Array of proxy IDs.
    """

    auto_select_enabled: bool = True
    proxy_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_select_enabled = self.auto_select_enabled

        proxy_ids: list[str] | Unset = UNSET
        if not isinstance(self.proxy_ids, Unset):
            proxy_ids = []
            for proxy_ids_item_data in self.proxy_ids:
                proxy_ids_item = str(proxy_ids_item_data)
                proxy_ids.append(proxy_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "autoSelectEnabled": auto_select_enabled,
            }
        )
        if proxy_ids is not UNSET:
            field_dict["proxyIds"] = proxy_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_select_enabled = d.pop("autoSelectEnabled")

        _proxy_ids = d.pop("proxyIds", UNSET)
        proxy_ids: list[UUID] | Unset = UNSET
        if _proxy_ids is not UNSET:
            proxy_ids = []
            for proxy_ids_item_data in _proxy_ids:
                proxy_ids_item = UUID(proxy_ids_item_data)

                proxy_ids.append(proxy_ids_item)

        backup_proxies_settings_model = cls(
            auto_select_enabled=auto_select_enabled,
            proxy_ids=proxy_ids,
        )

        backup_proxies_settings_model.additional_properties = d
        return backup_proxies_settings_model

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
