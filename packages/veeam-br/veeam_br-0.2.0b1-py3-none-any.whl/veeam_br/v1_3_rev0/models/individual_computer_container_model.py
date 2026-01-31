from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_individual_computer_connection_type import EIndividualComputerConnectionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_credentials_spec import LinuxCredentialsSpec


T = TypeVar("T", bound="IndividualComputerContainerModel")


@_attrs_define
class IndividualComputerContainerModel:
    """Individual computer container.

    Attributes:
        host_name (str): DNS name or IP address of the computer.
        connection_type (EIndividualComputerConnectionType): Authentication method for the protected computer.
        credentials_id (UUID | Unset): Credentials ID.
        single_use_credentials (LinuxCredentialsSpec | Unset): Settings for single-use credentials.
    """

    host_name: str
    connection_type: EIndividualComputerConnectionType
    credentials_id: UUID | Unset = UNSET
    single_use_credentials: LinuxCredentialsSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_name = self.host_name

        connection_type = self.connection_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        single_use_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.single_use_credentials, Unset):
            single_use_credentials = self.single_use_credentials.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostName": host_name,
                "connectionType": connection_type,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if single_use_credentials is not UNSET:
            field_dict["singleUseCredentials"] = single_use_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_credentials_spec import LinuxCredentialsSpec

        d = dict(src_dict)
        host_name = d.pop("hostName")

        connection_type = EIndividualComputerConnectionType(d.pop("connectionType"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _single_use_credentials = d.pop("singleUseCredentials", UNSET)
        single_use_credentials: LinuxCredentialsSpec | Unset
        if isinstance(_single_use_credentials, Unset):
            single_use_credentials = UNSET
        else:
            single_use_credentials = LinuxCredentialsSpec.from_dict(_single_use_credentials)

        individual_computer_container_model = cls(
            host_name=host_name,
            connection_type=connection_type,
            credentials_id=credentials_id,
            single_use_credentials=single_use_credentials,
        )

        individual_computer_container_model.additional_properties = d
        return individual_computer_container_model

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
