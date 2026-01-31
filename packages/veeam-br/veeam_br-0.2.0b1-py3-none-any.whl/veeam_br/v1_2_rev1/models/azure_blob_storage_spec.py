from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_blob_storage_account_model import AzureBlobStorageAccountModel
    from ..models.azure_blob_storage_container_model import AzureBlobStorageContainerModel
    from ..models.azure_storage_proxy_model import AzureStorageProxyModel
    from ..models.mount_server_settings_model import MountServerSettingsModel


T = TypeVar("T", bound="AzureBlobStorageSpec")


@_attrs_define
class AzureBlobStorageSpec:
    """Microsoft Azure Blob storage.

    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        account (AzureBlobStorageAccountModel): Account used to access the Azure Blob storage.
        container (AzureBlobStorageContainerModel): Azure Blob storage container.
        mount_server (MountServerSettingsModel): Settings for the mount server that is used for file and application
            items restore.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
        task_limit_enabled (bool | Unset): If `true`, the maximum number of concurrent tasks is limited.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
        proxy_appliance (AzureStorageProxyModel | Unset): Azure storage proxy appliance.
    """

    name: str
    description: str
    type_: ERepositoryType
    account: AzureBlobStorageAccountModel
    container: AzureBlobStorageContainerModel
    mount_server: MountServerSettingsModel
    unique_id: str | Unset = UNSET
    task_limit_enabled: bool | Unset = UNSET
    max_task_count: int | Unset = UNSET
    proxy_appliance: AzureStorageProxyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        account = self.account.to_dict()

        container = self.container.to_dict()

        mount_server = self.mount_server.to_dict()

        unique_id = self.unique_id

        task_limit_enabled = self.task_limit_enabled

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
                "type": type_,
                "account": account,
                "container": container,
                "mountServer": mount_server,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id
        if task_limit_enabled is not UNSET:
            field_dict["taskLimitEnabled"] = task_limit_enabled
        if max_task_count is not UNSET:
            field_dict["maxTaskCount"] = max_task_count
        if proxy_appliance is not UNSET:
            field_dict["proxyAppliance"] = proxy_appliance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_blob_storage_account_model import AzureBlobStorageAccountModel
        from ..models.azure_blob_storage_container_model import AzureBlobStorageContainerModel
        from ..models.azure_storage_proxy_model import AzureStorageProxyModel
        from ..models.mount_server_settings_model import MountServerSettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        account = AzureBlobStorageAccountModel.from_dict(d.pop("account"))

        container = AzureBlobStorageContainerModel.from_dict(d.pop("container"))

        mount_server = MountServerSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        task_limit_enabled = d.pop("taskLimitEnabled", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: AzureStorageProxyModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = AzureStorageProxyModel.from_dict(_proxy_appliance)

        azure_blob_storage_spec = cls(
            name=name,
            description=description,
            type_=type_,
            account=account,
            container=container,
            mount_server=mount_server,
            unique_id=unique_id,
            task_limit_enabled=task_limit_enabled,
            max_task_count=max_task_count,
            proxy_appliance=proxy_appliance,
        )

        azure_blob_storage_spec.additional_properties = d
        return azure_blob_storage_spec

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
