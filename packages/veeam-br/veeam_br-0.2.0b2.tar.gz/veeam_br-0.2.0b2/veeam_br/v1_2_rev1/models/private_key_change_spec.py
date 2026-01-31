from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PrivateKeyChangeSpec")


@_attrs_define
class PrivateKeyChangeSpec:
    """
    Attributes:
        private_key (str): New private key.
        passphrase (str | Unset): Passphrase that protects the private key.
    """

    private_key: str
    passphrase: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        private_key = self.private_key

        passphrase = self.passphrase

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "privateKey": private_key,
            }
        )
        if passphrase is not UNSET:
            field_dict["passphrase"] = passphrase

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        private_key = d.pop("privateKey")

        passphrase = d.pop("passphrase", UNSET)

        private_key_change_spec = cls(
            private_key=private_key,
            passphrase=passphrase,
        )

        private_key_change_spec.additional_properties = d
        return private_key_change_spec

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
