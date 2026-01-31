from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_server_account_model import AmazonS3ServerAccountModel
    from ..models.amazon_s3_server_processing_model import AmazonS3ServerProcessingModel


T = TypeVar("T", bound="AmazonS3ServerModel")


@_attrs_define
class AmazonS3ServerModel:
    """Amazon S3 object storage.

    Attributes:
        id (UUID): ID of the unstructured data server.
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        account (AmazonS3ServerAccountModel | Unset): Account for Amazon S3 object storage.
        processing (AmazonS3ServerProcessingModel | Unset): Processing settings for Amazon S3 object storage.
    """

    id: UUID
    type_: EUnstructuredDataServerType
    account: AmazonS3ServerAccountModel | Unset = UNSET
    processing: AmazonS3ServerProcessingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.account, Unset):
            account = self.account.to_dict()

        processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.processing, Unset):
            processing = self.processing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )
        if account is not UNSET:
            field_dict["account"] = account
        if processing is not UNSET:
            field_dict["processing"] = processing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_server_account_model import AmazonS3ServerAccountModel
        from ..models.amazon_s3_server_processing_model import AmazonS3ServerProcessingModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EUnstructuredDataServerType(d.pop("type"))

        _account = d.pop("account", UNSET)
        account: AmazonS3ServerAccountModel | Unset
        if isinstance(_account, Unset):
            account = UNSET
        else:
            account = AmazonS3ServerAccountModel.from_dict(_account)

        _processing = d.pop("processing", UNSET)
        processing: AmazonS3ServerProcessingModel | Unset
        if isinstance(_processing, Unset):
            processing = UNSET
        else:
            processing = AmazonS3ServerProcessingModel.from_dict(_processing)

        amazon_s3_server_model = cls(
            id=id,
            type_=type_,
            account=account,
            processing=processing,
        )

        amazon_s3_server_model.additional_properties = d
        return amazon_s3_server_model

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
