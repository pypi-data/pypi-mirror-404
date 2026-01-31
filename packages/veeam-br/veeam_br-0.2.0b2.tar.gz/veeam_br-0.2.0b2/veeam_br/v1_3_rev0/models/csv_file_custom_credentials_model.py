from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CSVFileCustomCredentialsModel")


@_attrs_define
class CSVFileCustomCredentialsModel:
    """Custom credentials for authenticating to associated computers.

    Attributes:
        use_master_credentials (bool): If `true`, master credentials are used to authenticate to the computers listed in
            a CSV file.
        credentials_id (UUID | Unset): ID of the credentials record used to authenticate to the computer.
        computer_name (str | Unset): DNS name or IP address of the computer.
    """

    use_master_credentials: bool
    credentials_id: UUID | Unset = UNSET
    computer_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_master_credentials = self.use_master_credentials

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        computer_name = self.computer_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useMasterCredentials": use_master_credentials,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if computer_name is not UNSET:
            field_dict["computerName"] = computer_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        use_master_credentials = d.pop("useMasterCredentials")

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        computer_name = d.pop("computerName", UNSET)

        csv_file_custom_credentials_model = cls(
            use_master_credentials=use_master_credentials,
            credentials_id=credentials_id,
            computer_name=computer_name,
        )

        csv_file_custom_credentials_model.additional_properties = d
        return csv_file_custom_credentials_model

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
