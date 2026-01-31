from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_connection_type import ERepositoryConnectionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ObjectStorageConnectionImportSpec")


@_attrs_define
class ObjectStorageConnectionImportSpec:
    """Object storage connection settings.

    Attributes:
        connection_type (ERepositoryConnectionType): Repository connection type (direct or through a gateway server).
        gateway_servers (list[str] | Unset): Array of gateway server IDs. The value is *null* if the connection type is
            *Direct*.
    """

    connection_type: ERepositoryConnectionType
    gateway_servers: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        connection_type = self.connection_type.value

        gateway_servers: list[str] | Unset = UNSET
        if not isinstance(self.gateway_servers, Unset):
            gateway_servers = self.gateway_servers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connectionType": connection_type,
            }
        )
        if gateway_servers is not UNSET:
            field_dict["gatewayServers"] = gateway_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        connection_type = ERepositoryConnectionType(d.pop("connectionType"))

        gateway_servers = cast(list[str], d.pop("gatewayServers", UNSET))

        object_storage_connection_import_spec = cls(
            connection_type=connection_type,
            gateway_servers=gateway_servers,
        )

        object_storage_connection_import_spec.additional_properties = d
        return object_storage_connection_import_spec

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
