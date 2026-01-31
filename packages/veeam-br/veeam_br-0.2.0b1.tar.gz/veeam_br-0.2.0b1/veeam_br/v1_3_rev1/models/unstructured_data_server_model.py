from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType

T = TypeVar("T", bound="UnstructuredDataServerModel")


@_attrs_define
class UnstructuredDataServerModel:
    """Unstructured data server.

    Attributes:
        id (UUID): ID of the unstructured data server.
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
    """

    id: UUID
    type_: EUnstructuredDataServerType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EUnstructuredDataServerType(d.pop("type"))

        unstructured_data_server_model = cls(
            id=id,
            type_=type_,
        )

        unstructured_data_server_model.additional_properties = d
        return unstructured_data_server_model

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
