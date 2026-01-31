from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType

if TYPE_CHECKING:
    from ..models.file_server_processing_model import FileServerProcessingModel


T = TypeVar("T", bound="FileServerSpec")


@_attrs_define
class FileServerSpec:
    """File server settings.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        host_id (UUID): Host ID. To get the ID, run the [Get All Servers](Managed-
            Servers#operation/GetAllManagedServers) request.
        processing (FileServerProcessingModel): File server processing settings.
    """

    type_: EUnstructuredDataServerType
    host_id: UUID
    processing: FileServerProcessingModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        host_id = str(self.host_id)

        processing = self.processing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "hostId": host_id,
                "processing": processing,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_server_processing_model import FileServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        processing = FileServerProcessingModel.from_dict(d.pop("processing"))

        file_server_spec = cls(
            type_=type_,
            host_id=host_id,
            processing=processing,
        )

        file_server_spec.additional_properties = d
        return file_server_spec

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
