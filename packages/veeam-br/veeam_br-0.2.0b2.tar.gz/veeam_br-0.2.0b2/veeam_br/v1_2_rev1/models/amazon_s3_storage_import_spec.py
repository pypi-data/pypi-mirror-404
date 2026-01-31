from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_storage_account_import_model import AmazonS3StorageAccountImportModel
    from ..models.amazon_s3_storage_bucket_model import AmazonS3StorageBucketModel
    from ..models.amazon_s3_storage_proxy_appliance_model import AmazonS3StorageProxyApplianceModel
    from ..models.mount_server_settings_import_spec import MountServerSettingsImportSpec


T = TypeVar("T", bound="AmazonS3StorageImportSpec")


@_attrs_define
class AmazonS3StorageImportSpec:
    """
    Attributes:
        name (str): Name of the object storage repository.
        description (str): Description of the object storage repository.
        unique_id (str): Unique ID that identifies the object storage repository.
        type_ (ERepositoryType): Repository type.
        account (AmazonS3StorageAccountImportModel): Account used to access the Amazon S3 storage.
        bucket (AmazonS3StorageBucketModel): Amazon S3 bucket where backup data is stored.
        mount_server (MountServerSettingsImportSpec): Settings for the mount server that is used for file and
            application items restore.
        enable_task_limit (bool | Unset): If `true`, the maximum number of concurrent tasks is limited.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
        proxy_appliance (AmazonS3StorageProxyApplianceModel | Unset): Amazon S3 proxy appliance.
    """

    name: str
    description: str
    unique_id: str
    type_: ERepositoryType
    account: AmazonS3StorageAccountImportModel
    bucket: AmazonS3StorageBucketModel
    mount_server: MountServerSettingsImportSpec
    enable_task_limit: bool | Unset = UNSET
    max_task_count: int | Unset = UNSET
    proxy_appliance: AmazonS3StorageProxyApplianceModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        type_ = self.type_.value

        account = self.account.to_dict()

        bucket = self.bucket.to_dict()

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
                "bucket": bucket,
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
        from ..models.amazon_s3_storage_account_import_model import AmazonS3StorageAccountImportModel
        from ..models.amazon_s3_storage_bucket_model import AmazonS3StorageBucketModel
        from ..models.amazon_s3_storage_proxy_appliance_model import AmazonS3StorageProxyApplianceModel
        from ..models.mount_server_settings_import_spec import MountServerSettingsImportSpec

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        type_ = ERepositoryType(d.pop("type"))

        account = AmazonS3StorageAccountImportModel.from_dict(d.pop("account"))

        bucket = AmazonS3StorageBucketModel.from_dict(d.pop("bucket"))

        mount_server = MountServerSettingsImportSpec.from_dict(d.pop("mountServer"))

        enable_task_limit = d.pop("enableTaskLimit", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: AmazonS3StorageProxyApplianceModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = AmazonS3StorageProxyApplianceModel.from_dict(_proxy_appliance)

        amazon_s3_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            type_=type_,
            account=account,
            bucket=bucket,
            mount_server=mount_server,
            enable_task_limit=enable_task_limit,
            max_task_count=max_task_count,
            proxy_appliance=proxy_appliance,
        )

        amazon_s3_storage_import_spec.additional_properties = d
        return amazon_s3_storage_import_spec

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
