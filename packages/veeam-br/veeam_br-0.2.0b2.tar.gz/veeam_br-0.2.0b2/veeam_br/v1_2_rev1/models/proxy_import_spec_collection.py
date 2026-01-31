from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.proxy_import_spec import ProxyImportSpec


T = TypeVar("T", bound="ProxyImportSpecCollection")


@_attrs_define
class ProxyImportSpecCollection:
    """
    Attributes:
        proxies (list[ProxyImportSpec]): Array of backup proxies.
    """

    proxies: list[ProxyImportSpec]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        proxies = []
        for proxies_item_data in self.proxies:
            proxies_item = proxies_item_data.to_dict()
            proxies.append(proxies_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "proxies": proxies,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.proxy_import_spec import ProxyImportSpec

        d = dict(src_dict)
        proxies = []
        _proxies = d.pop("proxies")
        for proxies_item_data in _proxies:
            proxies_item = ProxyImportSpec.from_dict(proxies_item_data)

            proxies.append(proxies_item)

        proxy_import_spec_collection = cls(
            proxies=proxies,
        )

        proxy_import_spec_collection.additional_properties = d
        return proxy_import_spec_collection

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
