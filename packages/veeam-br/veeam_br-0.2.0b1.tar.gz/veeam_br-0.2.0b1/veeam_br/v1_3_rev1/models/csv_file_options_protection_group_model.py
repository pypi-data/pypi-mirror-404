from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CSVFileOptionsProtectionGroupModel")


@_attrs_define
class CSVFileOptionsProtectionGroupModel:
    """CSV file settings.

    Attributes:
        path (str): Path to the CSV file.
        network_credentials_id (UUID | Unset): Network credentials ID.
    """

    path: str
    network_credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        network_credentials_id: str | Unset = UNSET
        if not isinstance(self.network_credentials_id, Unset):
            network_credentials_id = str(self.network_credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
            }
        )
        if network_credentials_id is not UNSET:
            field_dict["networkCredentialsId"] = network_credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        _network_credentials_id = d.pop("networkCredentialsId", UNSET)
        network_credentials_id: UUID | Unset
        if isinstance(_network_credentials_id, Unset):
            network_credentials_id = UNSET
        else:
            network_credentials_id = UUID(_network_credentials_id)

        csv_file_options_protection_group_model = cls(
            path=path,
            network_credentials_id=network_credentials_id,
        )

        csv_file_options_protection_group_model.additional_properties = d
        return csv_file_options_protection_group_model

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
