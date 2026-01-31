from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_login_grant_type import ELoginGrantType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RegisterVbrSpec")


@_attrs_define
class RegisterVbrSpec:
    """Settings for registering a backup server on the My Account portal. <div class="note"><strong>NOTE</strong> </br>
    This request only accepts the `authorization_code` login grant type. </div>

        Attributes:
            grant_type (ELoginGrantType): Authorization grant type.<p>Available values:<ul> <li>`password` — used to obtain
                an access token by providing a user name and password.</li> <li>`refresh_token` — used to refresh an expired or
                lost access token by providing a refresh token.</li> <li>`authorization_code` — used to obtain an access token
                by providing an authorization code.</li> <li>`vbr_token` — used to obtain an access token by providing a Veeam
                Backup & Replication token. This grant type is only used in a restricted mode for integration with Veeam Backup
                & Replication.</li></ul>
            code (str | Unset): Authorization code. Required if the `grant_type` value is `authorization_code`.
            code_verifier (str | Unset): Verifier code. Required if the `grant_type` value is `authorization_code`.
    """

    grant_type: ELoginGrantType
    code: str | Unset = UNSET
    code_verifier: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        grant_type = self.grant_type.value

        code = self.code

        code_verifier = self.code_verifier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "grant_type": grant_type,
            }
        )
        if code is not UNSET:
            field_dict["code"] = code
        if code_verifier is not UNSET:
            field_dict["codeVerifier"] = code_verifier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        grant_type = ELoginGrantType(d.pop("grant_type"))

        code = d.pop("code", UNSET)

        code_verifier = d.pop("codeVerifier", UNSET)

        register_vbr_spec = cls(
            grant_type=grant_type,
            code=code,
            code_verifier=code_verifier,
        )

        register_vbr_spec.additional_properties = d
        return register_vbr_spec

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
