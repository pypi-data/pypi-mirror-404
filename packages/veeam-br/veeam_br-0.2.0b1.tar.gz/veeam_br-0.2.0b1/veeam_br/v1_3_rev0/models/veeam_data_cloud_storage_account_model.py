from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_connection_model import ObjectStorageConnectionModel
    from ..models.veeam_data_cloud_vault_model import VeeamDataCloudVaultModel


T = TypeVar("T", bound="VeeamDataCloudStorageAccountModel")


@_attrs_define
class VeeamDataCloudStorageAccountModel:
    """Veeam Data Cloud Vault account.

    Attributes:
        vault (VeeamDataCloudVaultModel): Veeam Data Cloud Vault repository.
        connection_settings (ObjectStorageConnectionModel | Unset): Object storage connection settings.
    """

    vault: VeeamDataCloudVaultModel
    connection_settings: ObjectStorageConnectionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vault = self.vault.to_dict()

        connection_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.connection_settings, Unset):
            connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vault": vault,
            }
        )
        if connection_settings is not UNSET:
            field_dict["connectionSettings"] = connection_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_connection_model import ObjectStorageConnectionModel
        from ..models.veeam_data_cloud_vault_model import VeeamDataCloudVaultModel

        d = dict(src_dict)
        vault = VeeamDataCloudVaultModel.from_dict(d.pop("vault"))

        _connection_settings = d.pop("connectionSettings", UNSET)
        connection_settings: ObjectStorageConnectionModel | Unset
        if isinstance(_connection_settings, Unset):
            connection_settings = UNSET
        else:
            connection_settings = ObjectStorageConnectionModel.from_dict(_connection_settings)

        veeam_data_cloud_storage_account_model = cls(
            vault=vault,
            connection_settings=connection_settings,
        )

        veeam_data_cloud_storage_account_model.additional_properties = d
        return veeam_data_cloud_storage_account_model

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
