from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_access_type import ERepositoryAccessType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel


T = TypeVar("T", bound="RepositoryAccessPermissionsModel")


@_attrs_define
class RepositoryAccessPermissionsModel:
    """Repository access permissions.

    Attributes:
        access_policy (ERepositoryAccessType): Access type.
        accounts (list[str] | Unset): (For *AllowExplicit* access policy) Array of accounts that have access to the
            backup repository.
        encryption_settings (BackupStorageSettingsEncryptionModel | Unset): Encryption of backup files.
    """

    access_policy: ERepositoryAccessType
    accounts: list[str] | Unset = UNSET
    encryption_settings: BackupStorageSettingsEncryptionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_policy = self.access_policy.value

        accounts: list[str] | Unset = UNSET
        if not isinstance(self.accounts, Unset):
            accounts = self.accounts

        encryption_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.encryption_settings, Unset):
            encryption_settings = self.encryption_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accessPolicy": access_policy,
            }
        )
        if accounts is not UNSET:
            field_dict["accounts"] = accounts
        if encryption_settings is not UNSET:
            field_dict["encryptionSettings"] = encryption_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel

        d = dict(src_dict)
        access_policy = ERepositoryAccessType(d.pop("accessPolicy"))

        accounts = cast(list[str], d.pop("accounts", UNSET))

        _encryption_settings = d.pop("encryptionSettings", UNSET)
        encryption_settings: BackupStorageSettingsEncryptionModel | Unset
        if isinstance(_encryption_settings, Unset):
            encryption_settings = UNSET
        else:
            encryption_settings = BackupStorageSettingsEncryptionModel.from_dict(_encryption_settings)

        repository_access_permissions_model = cls(
            access_policy=access_policy,
            accounts=accounts,
            encryption_settings=encryption_settings,
        )

        repository_access_permissions_model.additional_properties = d
        return repository_access_permissions_model

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
