from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_servers_settings_model import MountServersSettingsModel
    from ..models.s3_compatible_proxy_model import S3CompatibleProxyModel
    from ..models.s3_compatible_storage_account_model import S3CompatibleStorageAccountModel
    from ..models.s3_compatible_storage_bucket_model import S3CompatibleStorageBucketModel


T = TypeVar("T", bound="S3CompatibleStorageModel")


@_attrs_define
class S3CompatibleStorageModel:
    """S3 compatible storage.

    Attributes:
        id (UUID): Backup repository ID.
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        account (S3CompatibleStorageAccountModel): Account used to access the S3 compatible storage.
        bucket (S3CompatibleStorageBucketModel): Bucket where backup data is stored.
        mount_server (MountServersSettingsModel): Mount server settings.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
        task_limit_enabled (bool | Unset): If `true`, the maximum number of concurrent tasks is limited.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
        proxy_appliance (S3CompatibleProxyModel | Unset): Proxy appliance for the S3 compatible storage.
    """

    id: UUID
    name: str
    description: str
    type_: ERepositoryType
    account: S3CompatibleStorageAccountModel
    bucket: S3CompatibleStorageBucketModel
    mount_server: MountServersSettingsModel
    unique_id: str | Unset = UNSET
    task_limit_enabled: bool | Unset = UNSET
    max_task_count: int | Unset = UNSET
    proxy_appliance: S3CompatibleProxyModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        account = self.account.to_dict()

        bucket = self.bucket.to_dict()

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
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "account": account,
                "bucket": bucket,
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
        from ..models.mount_servers_settings_model import MountServersSettingsModel
        from ..models.s3_compatible_proxy_model import S3CompatibleProxyModel
        from ..models.s3_compatible_storage_account_model import S3CompatibleStorageAccountModel
        from ..models.s3_compatible_storage_bucket_model import S3CompatibleStorageBucketModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        account = S3CompatibleStorageAccountModel.from_dict(d.pop("account"))

        bucket = S3CompatibleStorageBucketModel.from_dict(d.pop("bucket"))

        mount_server = MountServersSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        task_limit_enabled = d.pop("taskLimitEnabled", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: S3CompatibleProxyModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = S3CompatibleProxyModel.from_dict(_proxy_appliance)

        s3_compatible_storage_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            account=account,
            bucket=bucket,
            mount_server=mount_server,
            unique_id=unique_id,
            task_limit_enabled=task_limit_enabled,
            max_task_count=max_task_count,
            proxy_appliance=proxy_appliance,
        )

        s3_compatible_storage_model.additional_properties = d
        return s3_compatible_storage_model

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
