from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_server_processing_model import FileServerProcessingModel


T = TypeVar("T", bound="FileServerModel")


@_attrs_define
class FileServerModel:
    """File server.

    Attributes:
        id (UUID): ID of the unstructured data server.
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        host_id (UUID): Host ID.
        processing (FileServerProcessingModel): File server processing settings.
        name (str | Unset): DNS name of the file server.
    """

    id: UUID
    type_: EUnstructuredDataServerType
    host_id: UUID
    processing: FileServerProcessingModel
    name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        host_id = str(self.host_id)

        processing = self.processing.to_dict()

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "hostId": host_id,
                "processing": processing,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_server_processing_model import FileServerProcessingModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EUnstructuredDataServerType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        processing = FileServerProcessingModel.from_dict(d.pop("processing"))

        name = d.pop("name", UNSET)

        file_server_model = cls(
            id=id,
            type_=type_,
            host_id=host_id,
            processing=processing,
            name=name,
        )

        file_server_model.additional_properties = d
        return file_server_model

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
