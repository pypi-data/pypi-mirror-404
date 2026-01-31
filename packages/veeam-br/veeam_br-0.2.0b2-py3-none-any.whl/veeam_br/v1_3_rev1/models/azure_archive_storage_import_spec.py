from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_archive_storage_account_import_model import AzureArchiveStorageAccountImportModel
    from ..models.azure_archive_storage_container_model import AzureArchiveStorageContainerModel
    from ..models.azure_storage_proxy_model import AzureStorageProxyModel


T = TypeVar("T", bound="AzureArchiveStorageImportSpec")


@_attrs_define
class AzureArchiveStorageImportSpec:
    """Import settings for Microsoft Azure Archive storage.

    Attributes:
        name (str): Name of the object storage repository.
        description (str): Description of the object storage repository.
        unique_id (str): Unique ID that identifies the object storage repository.
        type_ (ERepositoryType): Repository type.
        account (AzureArchiveStorageAccountImportModel): Account used to access the Microsoft Azure Archive storage.
        container (AzureArchiveStorageContainerModel): Microsoft Azure Archive container where backup data is stored.
        proxy_appliance (AzureStorageProxyModel | Unset): Microsoft Azure storage proxy appliance.
    """

    name: str
    description: str
    unique_id: str
    type_: ERepositoryType
    account: AzureArchiveStorageAccountImportModel
    container: AzureArchiveStorageContainerModel
    proxy_appliance: AzureStorageProxyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        type_ = self.type_.value

        account = self.account.to_dict()

        container = self.container.to_dict()

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
            }
        )
        if proxy_appliance is not UNSET:
            field_dict["proxyAppliance"] = proxy_appliance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_archive_storage_account_import_model import AzureArchiveStorageAccountImportModel
        from ..models.azure_archive_storage_container_model import AzureArchiveStorageContainerModel
        from ..models.azure_storage_proxy_model import AzureStorageProxyModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        type_ = ERepositoryType(d.pop("type"))

        account = AzureArchiveStorageAccountImportModel.from_dict(d.pop("account"))

        container = AzureArchiveStorageContainerModel.from_dict(d.pop("container"))

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: AzureStorageProxyModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = AzureStorageProxyModel.from_dict(_proxy_appliance)

        azure_archive_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            type_=type_,
            account=account,
            container=container,
            proxy_appliance=proxy_appliance,
        )

        azure_archive_storage_import_spec.additional_properties = d
        return azure_archive_storage_import_spec

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
