from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_glacier_storage_bucket_model import AmazonS3GlacierStorageBucketModel
    from ..models.amazon_s3_storage_account_import_model import AmazonS3StorageAccountImportModel
    from ..models.amazon_s3_storage_proxy_appliance_model import AmazonS3StorageProxyApplianceModel


T = TypeVar("T", bound="AmazonS3GlacierStorageImportSpec")


@_attrs_define
class AmazonS3GlacierStorageImportSpec:
    """
    Attributes:
        name (str): Name of the object storage repository.
        description (str): Description of the object storage repository.
        unique_id (str): Unique ID that identifies the object storage repository.
        type_ (ERepositoryType): Repository type.
        account (AmazonS3StorageAccountImportModel): Account used to access the Amazon S3 storage.
        bucket (AmazonS3GlacierStorageBucketModel): Amazon S3 Glacier bucket where backup data is stored.
        proxy_appliance (AmazonS3StorageProxyApplianceModel | Unset): Amazon S3 proxy appliance.
    """

    name: str
    description: str
    unique_id: str
    type_: ERepositoryType
    account: AmazonS3StorageAccountImportModel
    bucket: AmazonS3GlacierStorageBucketModel
    proxy_appliance: AmazonS3StorageProxyApplianceModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        type_ = self.type_.value

        account = self.account.to_dict()

        bucket = self.bucket.to_dict()

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
            }
        )
        if proxy_appliance is not UNSET:
            field_dict["proxyAppliance"] = proxy_appliance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_glacier_storage_bucket_model import AmazonS3GlacierStorageBucketModel
        from ..models.amazon_s3_storage_account_import_model import AmazonS3StorageAccountImportModel
        from ..models.amazon_s3_storage_proxy_appliance_model import AmazonS3StorageProxyApplianceModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        type_ = ERepositoryType(d.pop("type"))

        account = AmazonS3StorageAccountImportModel.from_dict(d.pop("account"))

        bucket = AmazonS3GlacierStorageBucketModel.from_dict(d.pop("bucket"))

        _proxy_appliance = d.pop("proxyAppliance", UNSET)
        proxy_appliance: AmazonS3StorageProxyApplianceModel | Unset
        if isinstance(_proxy_appliance, Unset):
            proxy_appliance = UNSET
        else:
            proxy_appliance = AmazonS3StorageProxyApplianceModel.from_dict(_proxy_appliance)

        amazon_s3_glacier_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            type_=type_,
            account=account,
            bucket=bucket,
            proxy_appliance=proxy_appliance,
        )

        amazon_s3_glacier_storage_import_spec.additional_properties = d
        return amazon_s3_glacier_storage_import_spec

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
