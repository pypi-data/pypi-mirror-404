from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_archive_storage_account_model import AzureArchiveStorageAccountModel
    from ..models.azure_archive_storage_container_model import AzureArchiveStorageContainerModel
    from ..models.azure_storage_proxy_model import AzureStorageProxyModel


T = TypeVar("T", bound="AzureArchiveStorageSpec")


@_attrs_define
class AzureArchiveStorageSpec:
    """Microsoft Azure Archive storage.

    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        account (AzureArchiveStorageAccountModel): Account used to access the Microsoft Azure Archive storage.
        container (AzureArchiveStorageContainerModel): Microsoft Azure Archive container where backup data is stored.
        proxy_appliance (AzureStorageProxyModel): Microsoft Azure storage proxy appliance.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
        import_backup (bool | Unset): If `true`, Veeam Backup & Replication will search the repository for existing
            backups and import them automatically.
        import_index (bool | Unset): If `true`, Veeam Backup & Replication will import the guest OS file system index.
    """

    name: str
    description: str
    type_: ERepositoryType
    account: AzureArchiveStorageAccountModel
    container: AzureArchiveStorageContainerModel
    proxy_appliance: AzureStorageProxyModel
    unique_id: str | Unset = UNSET
    import_backup: bool | Unset = UNSET
    import_index: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        account = self.account.to_dict()

        container = self.container.to_dict()

        proxy_appliance = self.proxy_appliance.to_dict()

        unique_id = self.unique_id

        import_backup = self.import_backup

        import_index = self.import_index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "account": account,
                "container": container,
                "proxyAppliance": proxy_appliance,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id
        if import_backup is not UNSET:
            field_dict["importBackup"] = import_backup
        if import_index is not UNSET:
            field_dict["importIndex"] = import_index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_archive_storage_account_model import AzureArchiveStorageAccountModel
        from ..models.azure_archive_storage_container_model import AzureArchiveStorageContainerModel
        from ..models.azure_storage_proxy_model import AzureStorageProxyModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        account = AzureArchiveStorageAccountModel.from_dict(d.pop("account"))

        container = AzureArchiveStorageContainerModel.from_dict(d.pop("container"))

        proxy_appliance = AzureStorageProxyModel.from_dict(d.pop("proxyAppliance"))

        unique_id = d.pop("uniqueId", UNSET)

        import_backup = d.pop("importBackup", UNSET)

        import_index = d.pop("importIndex", UNSET)

        azure_archive_storage_spec = cls(
            name=name,
            description=description,
            type_=type_,
            account=account,
            container=container,
            proxy_appliance=proxy_appliance,
            unique_id=unique_id,
            import_backup=import_backup,
            import_index=import_index,
        )

        azure_archive_storage_spec.additional_properties = d
        return azure_archive_storage_spec

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
