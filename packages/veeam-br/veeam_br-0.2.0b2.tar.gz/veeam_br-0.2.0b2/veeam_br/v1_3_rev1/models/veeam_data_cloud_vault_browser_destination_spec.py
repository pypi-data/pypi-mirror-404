from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="VeeamDataCloudVaultBrowserDestinationSpec")


@_attrs_define
class VeeamDataCloudVaultBrowserDestinationSpec:
    """Settings for creating a new folder in Veeam Data Cloud Vault.

    Attributes:
        credentials_id (UUID): ID of a cloud credentials record required to connect to the object storage.
        service_type (ECloudServiceType): Type of cloud service.
        new_folder_name (str): Name of the new folder.
        vault_id (str): Vault ID.
        gateway_server_id (UUID | Unset): ID of a gateway server you want to use to connect to the object storage.
            Specify this parameter to check the internet connection of the server. As a gateway server, you can use the
            backup server or any Microsoft Windows or Linux server added to your backup infrastructure. By default, the
            backup server ID is used.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    new_folder_name: str
    vault_id: str
    gateway_server_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        new_folder_name = self.new_folder_name

        vault_id = self.vault_id

        gateway_server_id: str | Unset = UNSET
        if not isinstance(self.gateway_server_id, Unset):
            gateway_server_id = str(self.gateway_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "newFolderName": new_folder_name,
                "vaultId": vault_id,
            }
        )
        if gateway_server_id is not UNSET:
            field_dict["gatewayServerId"] = gateway_server_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        new_folder_name = d.pop("newFolderName")

        vault_id = d.pop("vaultId")

        _gateway_server_id = d.pop("gatewayServerId", UNSET)
        gateway_server_id: UUID | Unset
        if isinstance(_gateway_server_id, Unset):
            gateway_server_id = UNSET
        else:
            gateway_server_id = UUID(_gateway_server_id)

        veeam_data_cloud_vault_browser_destination_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            new_folder_name=new_folder_name,
            vault_id=vault_id,
            gateway_server_id=gateway_server_id,
        )

        veeam_data_cloud_vault_browser_destination_spec.additional_properties = d
        return veeam_data_cloud_vault_browser_destination_spec

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
