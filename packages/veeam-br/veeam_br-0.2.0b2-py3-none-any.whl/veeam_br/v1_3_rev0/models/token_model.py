from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TokenModel")


@_attrs_define
class TokenModel:
    """Authentication details.

    Attributes:
        access_token (str): String that represents authorization issued to the client. It must be specified in all
            requests. An access token can be used multiple times, but its lifetime is 15 minutes.
        token_type (str): Type of the access token.
        refresh_token (str): String that is used to obtain a new access token if the current access token expires or
            becomes lost. A refresh token can be used only once, and its default lifetime is 14 days.
        expires_in (int): Lifetime of the access token in seconds.
        issued (datetime.datetime): Date and time when the access token is issued.
        expires (datetime.datetime): Date and time when the access token expires.
    """

    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    issued: datetime.datetime
    expires: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        token_type = self.token_type

        refresh_token = self.refresh_token

        expires_in = self.expires_in

        issued = self.issued.isoformat()

        expires = self.expires.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "token_type": token_type,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                ".issued": issued,
                ".expires": expires,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("access_token")

        token_type = d.pop("token_type")

        refresh_token = d.pop("refresh_token")

        expires_in = d.pop("expires_in")

        issued = isoparse(d.pop(".issued"))

        expires = isoparse(d.pop(".expires"))

        token_model = cls(
            access_token=access_token,
            token_type=token_type,
            refresh_token=refresh_token,
            expires_in=expires_in,
            issued=issued,
            expires=expires,
        )

        token_model.additional_properties = d
        return token_model

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
