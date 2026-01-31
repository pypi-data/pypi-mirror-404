from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxy_type import EProxyType

T = TypeVar("T", bound="ProxyStateModel")


@_attrs_define
class ProxyStateModel:
    """Backup proxy state.

    Attributes:
        id (UUID): Backup proxy ID.
        name (str): Name of the backup proxy.
        description (str): Description of the backup proxy.
        type_ (EProxyType): Type of backup proxy.
        host_id (UUID): ID of the server.
        host_name (str): Name of the server.
        is_disabled (bool): If `true`, the proxy is disabled.
        is_online (bool): If `true`, the proxy is online.
        is_out_of_date (bool): If `true`, the proxy components are outdated.
    """

    id: UUID
    name: str
    description: str
    type_: EProxyType
    host_id: UUID
    host_name: str
    is_disabled: bool
    is_online: bool
    is_out_of_date: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        host_id = str(self.host_id)

        host_name = self.host_name

        is_disabled = self.is_disabled

        is_online = self.is_online

        is_out_of_date = self.is_out_of_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "hostId": host_id,
                "hostName": host_name,
                "isDisabled": is_disabled,
                "isOnline": is_online,
                "isOutOfDate": is_out_of_date,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EProxyType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        host_name = d.pop("hostName")

        is_disabled = d.pop("isDisabled")

        is_online = d.pop("isOnline")

        is_out_of_date = d.pop("isOutOfDate")

        proxy_state_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            host_id=host_id,
            host_name=host_name,
            is_disabled=is_disabled,
            is_online=is_online,
            is_out_of_date=is_out_of_date,
        )

        proxy_state_model.additional_properties = d
        return proxy_state_model

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
