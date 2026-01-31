from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_credentials_existing_account_spec import AzureComputeCredentialsExistingAccountSpec


T = TypeVar("T", bound="AzureComputeCloudCredentialsImportSpec")


@_attrs_define
class AzureComputeCloudCredentialsImportSpec:
    """
    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        unique_id (str): Unique ID that identifies the cloud credentials record.
        connection_name (str): Name under which the cloud credentials record is shown in Veeam Backup & Replication.
        existing_account (AzureComputeCredentialsExistingAccountSpec): Existing Microsoft Entra ID app registration.
        description (str | Unset): Description of the cloud credentials record.
    """

    type_: ECloudCredentialsType
    unique_id: str
    connection_name: str
    existing_account: AzureComputeCredentialsExistingAccountSpec
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        unique_id = self.unique_id

        connection_name = self.connection_name

        existing_account = self.existing_account.to_dict()

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "uniqueId": unique_id,
                "connectionName": connection_name,
                "existingAccount": existing_account,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_credentials_existing_account_spec import AzureComputeCredentialsExistingAccountSpec

        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        unique_id = d.pop("uniqueId")

        connection_name = d.pop("connectionName")

        existing_account = AzureComputeCredentialsExistingAccountSpec.from_dict(d.pop("existingAccount"))

        description = d.pop("description", UNSET)

        azure_compute_cloud_credentials_import_spec = cls(
            type_=type_,
            unique_id=unique_id,
            connection_name=connection_name,
            existing_account=existing_account,
            description=description,
        )

        azure_compute_cloud_credentials_import_spec.additional_properties = d
        return azure_compute_cloud_credentials_import_spec

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
