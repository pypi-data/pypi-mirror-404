from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxy_type import EProxyType

if TYPE_CHECKING:
    from ..models.proxy_server_settings_import_spec import ProxyServerSettingsImportSpec


T = TypeVar("T", bound="ProxyImportSpec")


@_attrs_define
class ProxyImportSpec:
    """
    Attributes:
        description (str): Description of the backup proxy.
        type_ (EProxyType): Type of the backup proxy.
        server (ProxyServerSettingsImportSpec): Settings of the server that is used as a backup proxy.
    """

    description: str
    type_: EProxyType
    server: ProxyServerSettingsImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        type_ = self.type_.value

        server = self.server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "type": type_,
                "server": server,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.proxy_server_settings_import_spec import ProxyServerSettingsImportSpec

        d = dict(src_dict)
        description = d.pop("description")

        type_ = EProxyType(d.pop("type"))

        server = ProxyServerSettingsImportSpec.from_dict(d.pop("server"))

        proxy_import_spec = cls(
            description=description,
            type_=type_,
            server=server,
        )

        proxy_import_spec.additional_properties = d
        return proxy_import_spec

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
