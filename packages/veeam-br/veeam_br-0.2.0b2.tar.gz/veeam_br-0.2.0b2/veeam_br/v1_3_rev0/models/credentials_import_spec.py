from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_linux_settings_import_model import CredentialsLinuxSettingsImportModel


T = TypeVar("T", bound="CredentialsImportSpec")


@_attrs_define
class CredentialsImportSpec:
    """Credential import settings.

    Attributes:
        username (str): User name.
        unique_id (str): Unique ID that identifies the credentials record.
        type_ (ECredentialsType): Credentials type.
        password (str | Unset): Password.
        description (str | Unset): Description of the credentials record.
        linux_additional_settings (CredentialsLinuxSettingsImportModel | Unset): Additional Linux account settings.
    """

    username: str
    unique_id: str
    type_: ECredentialsType
    password: str | Unset = UNSET
    description: str | Unset = UNSET
    linux_additional_settings: CredentialsLinuxSettingsImportModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        unique_id = self.unique_id

        type_ = self.type_.value

        password = self.password

        description = self.description

        linux_additional_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux_additional_settings, Unset):
            linux_additional_settings = self.linux_additional_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "uniqueId": unique_id,
                "type": type_,
            }
        )
        if password is not UNSET:
            field_dict["password"] = password
        if description is not UNSET:
            field_dict["description"] = description
        if linux_additional_settings is not UNSET:
            field_dict["linuxAdditionalSettings"] = linux_additional_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_linux_settings_import_model import CredentialsLinuxSettingsImportModel

        d = dict(src_dict)
        username = d.pop("username")

        unique_id = d.pop("uniqueId")

        type_ = ECredentialsType(d.pop("type"))

        password = d.pop("password", UNSET)

        description = d.pop("description", UNSET)

        _linux_additional_settings = d.pop("linuxAdditionalSettings", UNSET)
        linux_additional_settings: CredentialsLinuxSettingsImportModel | Unset
        if isinstance(_linux_additional_settings, Unset):
            linux_additional_settings = UNSET
        else:
            linux_additional_settings = CredentialsLinuxSettingsImportModel.from_dict(_linux_additional_settings)

        credentials_import_spec = cls(
            username=username,
            unique_id=unique_id,
            type_=type_,
            password=password,
            description=description,
            linux_additional_settings=linux_additional_settings,
        )

        credentials_import_spec.additional_properties = d
        return credentials_import_spec

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
