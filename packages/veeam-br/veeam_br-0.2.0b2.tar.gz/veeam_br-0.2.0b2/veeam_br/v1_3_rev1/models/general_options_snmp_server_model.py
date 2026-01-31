from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GeneralOptionsSNMPServerModel")


@_attrs_define
class GeneralOptionsSNMPServerModel:
    """SNMP server settings.

    Attributes:
        receiver (str): Full DNS name or IP address of the SNMP server.
        port (int): Port on the SNMP server.
        community_string (str): SNMP community string.
    """

    receiver: str
    port: int
    community_string: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        receiver = self.receiver

        port = self.port

        community_string = self.community_string

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "receiver": receiver,
                "port": port,
                "communityString": community_string,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        receiver = d.pop("receiver")

        port = d.pop("port")

        community_string = d.pop("communityString")

        general_options_snmp_server_model = cls(
            receiver=receiver,
            port=port,
            community_string=community_string,
        )

        general_options_snmp_server_model.additional_properties = d
        return general_options_snmp_server_model

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
