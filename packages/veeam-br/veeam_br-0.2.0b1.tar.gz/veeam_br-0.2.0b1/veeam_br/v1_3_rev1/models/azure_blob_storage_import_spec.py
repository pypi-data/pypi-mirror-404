from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_blob_storage_account_import_model import AzureBlobStorageAccountImportModel
    from ..models.azure_blob_storage_container_model import AzureBlobStorageContainerModel
    from ..models.azure_storage_proxy_model import AzureStorageProxyModel
    from ..models.mount_servers_settings_import_spec import MountServersSettingsImportSpec


T = TypeVar("T", bound="AzureBlobStorageImportSpec")


@_attrs_define
class AzureBlobStorageImportSpec:
    """Import settings for Microsoft Azure Blob storage repository.

    Attributes:
        name (str): Name of the object storage repository.
        description (str): Description of the object storage repository.
        unique_id (str): Unique ID that identifies the object storage repository.
        type_ (ERepositoryType): Repository type.
        account (AzureBlobStorageAccountImportModel): Account used to access the Microsoft Azure Blob storage.
        container (AzureBlobStorageContainerModel): Microsoft Azure Blob storage container.
        mount_server (MountServersSettingsImportSpec): Import settings for mount servers.
        enable_task_limit (bool | Unset): If `true`, the maximum number of concurrent tasks is limited.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
        proxy_appliance (AzureStorageProxyModel | Unset): Microsoft Azure storage proxy appliance.
    """

    name: str
    description: str
    unique_id: str
    type_: ERepositoryType
    account: AzureBlobStorageAccountImportModel
    container: AzureBlobStorageContainerModel
    mount_server: MountServersSettingsImportSpec
    enable_task_limit: bool | Unset = UNSET
    max_task_count: int | Unset = UNSET
    proxy_appliance: AzureStorageProxyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        type_ = self.type_.value

        account = self.account.to_dict()

        container = self.container.to_dict()

        mount_server = self.mount_server.to_dict()

        enable_task_limit = self.enable_task_limit

        max_task_count = self.max_task_count

        proxy_appliance: dict[str, Any] | Unset = UNSET
        if not isinstance(self.proxy_appliance, Unset):
            proxy_appliance = self.proxy_appliance.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "uniqueId": unique_id,
                "type": type_,
                "account": account,
                "container": container,
                "mountServer": mount_server,
            }
        )
        if enable_task_limit is not UNSET:
            field_dict["enableTaskLimit"] = enable_task_limit
        if max_task_count is not UNSET:
            field_dict["maxTaskCount"] = max_task_count
        if proxy_appliance is not UNSET:
            field_dict["proxyAppliance"] = proxy_appliance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_blob_storage_account_import_model import AzureBlobStorageAccountImportModel
        from ..models.azure_blob_storage_container_model import AzureBlobStorageContainerModel
        from ..models.azure_storage_proxy_model import AzureStorageProxyModel
        from ..models.mount_servers_settings_import_spec import MountServersSettingsImportSpec

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        type_ = ERepositoryType(d.pop("type"))

        account = AzureBlobStorageAccountImportModel.from_dict(d.pop("account"))

        container = AzureBlobStorageContainerModel.from_dict(d.pop("container"))

        mount_server = MountServersSettingsImportSpec.from_dict(d.pop("mountServer"))

        enable_task_limit = d.pop("enableTaskLimit", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: AzureStorageProxyModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = AzureStorageProxyModel.from_dict(_proxy_appliance)

        azure_blob_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            type_=type_,
            account=account,
            container=container,
            mount_server=mount_server,
            enable_task_limit=enable_task_limit,
            max_task_count=max_task_count,
            proxy_appliance=proxy_appliance,
        )

        azure_blob_storage_import_spec.additional_properties = d
        return azure_blob_storage_import_spec

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
