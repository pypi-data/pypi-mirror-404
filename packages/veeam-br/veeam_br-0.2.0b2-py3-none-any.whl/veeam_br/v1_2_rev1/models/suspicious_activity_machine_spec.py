from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SuspiciousActivityMachineSpec")


@_attrs_define
class SuspiciousActivityMachineSpec:
    """Machine that you want to mark with the malware event. Specify at least 2 parameters.<p> Note that Veeam Backup &
    Replication can identify a machine by its FQDN, IPv4 address and IPv6 address only if the machine has been powered
    on during the backup. If you back up a powered-off machine, Veeam Backup & Replication will not get the machine IP
    addresses and domain name and will not be able to identify the machine.</p>

        Attributes:
            fqdn (str | Unset): Fully Qualified Domain Name of the machine.
            ipv4 (str | Unset): IPv4 address of machine.
            ipv6 (str | Unset): IPv6 address of the machine.
            uuid (str | Unset): BIOS UUID of the machine. Specify the UUID in the 8-4-4-4-12 format&#58; xxxxxxxx-xxxx-xxxx-
                xxxx-xxxxxxxxxxxx.
    """

    fqdn: str | Unset = UNSET
    ipv4: str | Unset = UNSET
    ipv6: str | Unset = UNSET
    uuid: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fqdn = self.fqdn

        ipv4 = self.ipv4

        ipv6 = self.ipv6

        uuid = self.uuid

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if fqdn is not UNSET:
            field_dict["fqdn"] = fqdn
        if ipv4 is not UNSET:
            field_dict["ipv4"] = ipv4
        if ipv6 is not UNSET:
            field_dict["ipv6"] = ipv6
        if uuid is not UNSET:
            field_dict["uuid"] = uuid

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        fqdn = d.pop("fqdn", UNSET)

        ipv4 = d.pop("ipv4", UNSET)

        ipv6 = d.pop("ipv6", UNSET)

        uuid = d.pop("uuid", UNSET)

        suspicious_activity_machine_spec = cls(
            fqdn=fqdn,
            ipv4=ipv4,
            ipv6=ipv6,
            uuid=uuid,
        )

        suspicious_activity_machine_spec.additional_properties = d
        return suspicious_activity_machine_spec

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
