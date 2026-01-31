from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="VeeamRegistrationInfo")


@_attrs_define
class VeeamRegistrationInfo:
    """Details on registering a backup server on the My Account portal.

    Attributes:
        is_registered (bool): If `true`, the backup server is registered on the My Account portal.
        expiration_date (datetime.datetime | Unset): Expiration date of registration on the My Account portal.
        thumprint (str | Unset): Thumprint of the certificate that is uploaded to the My Account portal.
    """

    is_registered: bool
    expiration_date: datetime.datetime | Unset = UNSET
    thumprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_registered = self.is_registered

        expiration_date: str | Unset = UNSET
        if not isinstance(self.expiration_date, Unset):
            expiration_date = self.expiration_date.isoformat()

        thumprint = self.thumprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isRegistered": is_registered,
            }
        )
        if expiration_date is not UNSET:
            field_dict["expirationDate"] = expiration_date
        if thumprint is not UNSET:
            field_dict["thumprint"] = thumprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_registered = d.pop("isRegistered")

        _expiration_date = d.pop("expirationDate", UNSET)
        expiration_date: datetime.datetime | Unset
        if isinstance(_expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = isoparse(_expiration_date)

        thumprint = d.pop("thumprint", UNSET)

        veeam_registration_info = cls(
            is_registered=is_registered,
            expiration_date=expiration_date,
            thumprint=thumprint,
        )

        veeam_registration_info.additional_properties = d
        return veeam_registration_info

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
