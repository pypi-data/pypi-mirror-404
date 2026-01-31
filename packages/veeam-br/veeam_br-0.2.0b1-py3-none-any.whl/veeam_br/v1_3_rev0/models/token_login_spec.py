from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_login_grant_type import ELoginGrantType
from ..types import UNSET, Unset

T = TypeVar("T", bound="TokenLoginSpec")


@_attrs_define
class TokenLoginSpec:
    """Authentication settings.

    Attributes:
        grant_type (ELoginGrantType): Authorization grant type.<p>Available values:<ul> <li>`password` — used to obtain
            an access token by providing a user name and password.</li> <li>`refresh_token` — used to refresh an expired or
            lost access token by providing a refresh token.</li> <li>`authorization_code` — used to obtain an access token
            by providing an authorization code.</li> <li>`vbr_token` — used to obtain an access token by providing a Veeam
            Backup & Replication token. This grant type is only used in a restricted mode for integration with Veeam Backup
            & Replication.</li></ul>
        username (str | Unset): User name. Required if the `grant_type` value is `password`.
        password (str | Unset): Password. Required if the `grant_type` value is `password`.
        refresh_token (str | Unset): Refresh token. Required if the `grant_type` value is `refresh_token`.
        code (str | Unset): Authorization code. Required if the `grant_type` value is `authorization_code`.
        use_short_term_refresh (bool | Unset): If `true`, a short-term refresh token is used. Lifetime of the short-term
            refresh token is the access token lifetime plus 15 minutes.
        vbr_token (str | Unset): Veeam Backup & Replication platform service token.
    """

    grant_type: ELoginGrantType
    username: str | Unset = UNSET
    password: str | Unset = UNSET
    refresh_token: str | Unset = UNSET
    code: str | Unset = UNSET
    use_short_term_refresh: bool | Unset = UNSET
    vbr_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        grant_type = self.grant_type.value

        username = self.username

        password = self.password

        refresh_token = self.refresh_token

        code = self.code

        use_short_term_refresh = self.use_short_term_refresh

        vbr_token = self.vbr_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "grant_type": grant_type,
            }
        )
        if username is not UNSET:
            field_dict["username"] = username
        if password is not UNSET:
            field_dict["password"] = password
        if refresh_token is not UNSET:
            field_dict["refresh_token"] = refresh_token
        if code is not UNSET:
            field_dict["code"] = code
        if use_short_term_refresh is not UNSET:
            field_dict["use_short_term_refresh"] = use_short_term_refresh
        if vbr_token is not UNSET:
            field_dict["vbr_token"] = vbr_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        grant_type = ELoginGrantType(d.pop("grant_type"))

        username = d.pop("username", UNSET)

        password = d.pop("password", UNSET)

        refresh_token = d.pop("refresh_token", UNSET)

        code = d.pop("code", UNSET)

        use_short_term_refresh = d.pop("use_short_term_refresh", UNSET)

        vbr_token = d.pop("vbr_token", UNSET)

        token_login_spec = cls(
            grant_type=grant_type,
            username=username,
            password=password,
            refresh_token=refresh_token,
            code=code,
            use_short_term_refresh=use_short_term_refresh,
            vbr_token=vbr_token,
        )

        token_login_spec.additional_properties = d
        return token_login_spec

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
