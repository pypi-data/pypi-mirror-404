from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.veeam_data_cloud_vault_model import VeeamDataCloudVaultModel


T = TypeVar("T", bound="VeeamDataCloudVaultStorageBrowserModel")


@_attrs_define
class VeeamDataCloudVaultStorageBrowserModel:
    """Veeam Data Cloud Vault.

    Attributes:
        credentials_id (UUID): ID of the cloud credentials record.
        service_type (ECloudServiceType): Type of cloud service.
        vaults (list[VeeamDataCloudVaultModel]): Array of Veeam Data Cloud Vault repositories.
        gateway_server_id (UUID | Unset): ID of a gateway server you want to use to connect to the object storage.
            Specify this parameter to check internet connection of the server. As a gateway server you can use the backup
            server or any Microsoft Windows or Linux server added to your backup infrastructure. By default, the backup
            server ID is used.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    vaults: list[VeeamDataCloudVaultModel]
    gateway_server_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        vaults = []
        for vaults_item_data in self.vaults:
            vaults_item = vaults_item_data.to_dict()
            vaults.append(vaults_item)

        gateway_server_id: str | Unset = UNSET
        if not isinstance(self.gateway_server_id, Unset):
            gateway_server_id = str(self.gateway_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "vaults": vaults,
            }
        )
        if gateway_server_id is not UNSET:
            field_dict["gatewayServerId"] = gateway_server_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.veeam_data_cloud_vault_model import VeeamDataCloudVaultModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        vaults = []
        _vaults = d.pop("vaults")
        for vaults_item_data in _vaults:
            vaults_item = VeeamDataCloudVaultModel.from_dict(vaults_item_data)

            vaults.append(vaults_item)

        _gateway_server_id = d.pop("gatewayServerId", UNSET)
        gateway_server_id: UUID | Unset
        if isinstance(_gateway_server_id, Unset):
            gateway_server_id = UNSET
        else:
            gateway_server_id = UUID(_gateway_server_id)

        veeam_data_cloud_vault_storage_browser_model = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            vaults=vaults,
            gateway_server_id=gateway_server_id,
        )

        veeam_data_cloud_vault_storage_browser_model.additional_properties = d
        return veeam_data_cloud_vault_storage_browser_model

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
