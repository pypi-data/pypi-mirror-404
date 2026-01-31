from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType

if TYPE_CHECKING:
    from ..models.amazon_s3_server_account_model import AmazonS3ServerAccountModel
    from ..models.amazon_s3_server_processing_model import AmazonS3ServerProcessingModel


T = TypeVar("T", bound="AmazonS3ServerSpec")


@_attrs_define
class AmazonS3ServerSpec:
    """Settings for Amazon S3 object storage.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        account (AmazonS3ServerAccountModel): Account for Amazon S3 object storage.
        processing (AmazonS3ServerProcessingModel): Processing settings for Amazon S3 object storage.
    """

    type_: EUnstructuredDataServerType
    account: AmazonS3ServerAccountModel
    processing: AmazonS3ServerProcessingModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        account = self.account.to_dict()

        processing = self.processing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "account": account,
                "processing": processing,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_server_account_model import AmazonS3ServerAccountModel
        from ..models.amazon_s3_server_processing_model import AmazonS3ServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        account = AmazonS3ServerAccountModel.from_dict(d.pop("account"))

        processing = AmazonS3ServerProcessingModel.from_dict(d.pop("processing"))

        amazon_s3_server_spec = cls(
            type_=type_,
            account=account,
            processing=processing,
        )

        amazon_s3_server_spec.additional_properties = d
        return amazon_s3_server_spec

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
