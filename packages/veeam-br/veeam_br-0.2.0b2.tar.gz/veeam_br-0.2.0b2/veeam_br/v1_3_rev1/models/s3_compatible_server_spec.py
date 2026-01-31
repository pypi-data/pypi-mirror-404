from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType

if TYPE_CHECKING:
    from ..models.s3_compatible_server_account_model import S3CompatibleServerAccountModel
    from ..models.s3_compatible_server_processing_model import S3CompatibleServerProcessingModel


T = TypeVar("T", bound="S3CompatibleServerSpec")


@_attrs_define
class S3CompatibleServerSpec:
    """Settings for S3 compatible object storage.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        account (S3CompatibleServerAccountModel): Account for S3 compatible object storage.
        processing (S3CompatibleServerProcessingModel): Processing settings for S3 compatible object storage.
    """

    type_: EUnstructuredDataServerType
    account: S3CompatibleServerAccountModel
    processing: S3CompatibleServerProcessingModel
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
        from ..models.s3_compatible_server_account_model import S3CompatibleServerAccountModel
        from ..models.s3_compatible_server_processing_model import S3CompatibleServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        account = S3CompatibleServerAccountModel.from_dict(d.pop("account"))

        processing = S3CompatibleServerProcessingModel.from_dict(d.pop("processing"))

        s3_compatible_server_spec = cls(
            type_=type_,
            account=account,
            processing=processing,
        )

        s3_compatible_server_spec.additional_properties = d
        return s3_compatible_server_spec

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
