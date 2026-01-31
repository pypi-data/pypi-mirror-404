from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_compute_credentials_creation_mode import EAzureComputeCredentialsCreationMode
from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_credentials_existing_account_spec import AzureComputeCredentialsExistingAccountSpec
    from ..models.azure_compute_credentials_new_account_spec import AzureComputeCredentialsNewAccountSpec


T = TypeVar("T", bound="AzureComputeCloudCredentialsSpec")


@_attrs_define
class AzureComputeCloudCredentialsSpec:
    """Settings for Microsoft Azure compute account credentials.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        connection_name (str): Name under which the cloud credentials record will be shown in Veeam Backup &
            Replication.
        creation_mode (EAzureComputeCredentialsCreationMode): Connection method that defines whether you want to connect
            to Microsoft Entra ID using an existing or a newly created app registration.
        description (str | Unset): Description of the cloud credentials record.
        existing_account (AzureComputeCredentialsExistingAccountSpec | Unset): Existing Microsoft Entra ID app
            registration.
        new_account (AzureComputeCredentialsNewAccountSpec | Unset): New Microsoft Entra ID app registration.
        unique_id (str | Unset): Unique ID that identifies the cloud credentials record.
    """

    type_: ECloudCredentialsType
    connection_name: str
    creation_mode: EAzureComputeCredentialsCreationMode
    description: str | Unset = UNSET
    existing_account: AzureComputeCredentialsExistingAccountSpec | Unset = UNSET
    new_account: AzureComputeCredentialsNewAccountSpec | Unset = UNSET
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        connection_name = self.connection_name

        creation_mode = self.creation_mode.value

        description = self.description

        existing_account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.existing_account, Unset):
            existing_account = self.existing_account.to_dict()

        new_account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.new_account, Unset):
            new_account = self.new_account.to_dict()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "connectionName": connection_name,
                "creationMode": creation_mode,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if existing_account is not UNSET:
            field_dict["existingAccount"] = existing_account
        if new_account is not UNSET:
            field_dict["newAccount"] = new_account
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_credentials_existing_account_spec import AzureComputeCredentialsExistingAccountSpec
        from ..models.azure_compute_credentials_new_account_spec import AzureComputeCredentialsNewAccountSpec

        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        connection_name = d.pop("connectionName")

        creation_mode = EAzureComputeCredentialsCreationMode(d.pop("creationMode"))

        description = d.pop("description", UNSET)

        _existing_account = d.pop("existingAccount", UNSET)
        existing_account: AzureComputeCredentialsExistingAccountSpec | Unset
        if isinstance(_existing_account, Unset):
            existing_account = UNSET
        else:
            existing_account = AzureComputeCredentialsExistingAccountSpec.from_dict(_existing_account)

        _new_account = d.pop("newAccount", UNSET)
        new_account: AzureComputeCredentialsNewAccountSpec | Unset
        if isinstance(_new_account, Unset):
            new_account = UNSET
        else:
            new_account = AzureComputeCredentialsNewAccountSpec.from_dict(_new_account)

        unique_id = d.pop("uniqueId", UNSET)

        azure_compute_cloud_credentials_spec = cls(
            type_=type_,
            connection_name=connection_name,
            creation_mode=creation_mode,
            description=description,
            existing_account=existing_account,
            new_account=new_account,
            unique_id=unique_id,
        )

        azure_compute_cloud_credentials_spec.additional_properties = d
        return azure_compute_cloud_credentials_spec

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
