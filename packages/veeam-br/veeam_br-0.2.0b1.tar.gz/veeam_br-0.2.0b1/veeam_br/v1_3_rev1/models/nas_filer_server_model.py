from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.nas_filer_server_processing_model import NASFilerServerProcessingModel


T = TypeVar("T", bound="NASFilerServerModel")


@_attrs_define
class NASFilerServerModel:
    """NAS filer.

    Attributes:
        id (UUID): ID of the unstructured data server.
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        storage_host_id (UUID): Storage host ID.
        processing (NASFilerServerProcessingModel): NAS filer processing settings.
        name (str | Unset): DNS name of the NAS filer.
        access_credentials_required (bool | Unset): If `true`, credentials are required to access the share.
        access_credentials_id (UUID | Unset): ID of the credential record used to access the share.
    """

    id: UUID
    type_: EUnstructuredDataServerType
    storage_host_id: UUID
    processing: NASFilerServerProcessingModel
    name: str | Unset = UNSET
    access_credentials_required: bool | Unset = UNSET
    access_credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        storage_host_id = str(self.storage_host_id)

        processing = self.processing.to_dict()

        name = self.name

        access_credentials_required = self.access_credentials_required

        access_credentials_id: str | Unset = UNSET
        if not isinstance(self.access_credentials_id, Unset):
            access_credentials_id = str(self.access_credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "storageHostId": storage_host_id,
                "processing": processing,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if access_credentials_required is not UNSET:
            field_dict["accessCredentialsRequired"] = access_credentials_required
        if access_credentials_id is not UNSET:
            field_dict["accessCredentialsId"] = access_credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.nas_filer_server_processing_model import NASFilerServerProcessingModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EUnstructuredDataServerType(d.pop("type"))

        storage_host_id = UUID(d.pop("storageHostId"))

        processing = NASFilerServerProcessingModel.from_dict(d.pop("processing"))

        name = d.pop("name", UNSET)

        access_credentials_required = d.pop("accessCredentialsRequired", UNSET)

        _access_credentials_id = d.pop("accessCredentialsId", UNSET)
        access_credentials_id: UUID | Unset
        if isinstance(_access_credentials_id, Unset):
            access_credentials_id = UNSET
        else:
            access_credentials_id = UUID(_access_credentials_id)

        nas_filer_server_model = cls(
            id=id,
            type_=type_,
            storage_host_id=storage_host_id,
            processing=processing,
            name=name,
            access_credentials_required=access_credentials_required,
            access_credentials_id=access_credentials_id,
        )

        nas_filer_server_model.additional_properties = d
        return nas_filer_server_model

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
