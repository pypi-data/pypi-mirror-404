from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_browse_properties import FlrBrowseProperties
    from ..models.unstructured_data_browse_source_properties import UnstructuredDataBrowseSourceProperties


T = TypeVar("T", bound="UnstructuredDataFlrBrowseMountModel")


@_attrs_define
class UnstructuredDataFlrBrowseMountModel:
    """
    Attributes:
        session_id (UUID): Restore session ID.
        properties (FlrBrowseProperties | Unset): Browser properties.
        source_properties (UnstructuredDataBrowseSourceProperties | Unset): Properties of unstructured data backup.
    """

    session_id: UUID
    properties: FlrBrowseProperties | Unset = UNSET
    source_properties: UnstructuredDataBrowseSourceProperties | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = str(self.session_id)

        properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.properties, Unset):
            properties = self.properties.to_dict()

        source_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.source_properties, Unset):
            source_properties = self.source_properties.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sessionId": session_id,
            }
        )
        if properties is not UNSET:
            field_dict["properties"] = properties
        if source_properties is not UNSET:
            field_dict["sourceProperties"] = source_properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_browse_properties import FlrBrowseProperties
        from ..models.unstructured_data_browse_source_properties import UnstructuredDataBrowseSourceProperties

        d = dict(src_dict)
        session_id = UUID(d.pop("sessionId"))

        _properties = d.pop("properties", UNSET)
        properties: FlrBrowseProperties | Unset
        if isinstance(_properties, Unset):
            properties = UNSET
        else:
            properties = FlrBrowseProperties.from_dict(_properties)

        _source_properties = d.pop("sourceProperties", UNSET)
        source_properties: UnstructuredDataBrowseSourceProperties | Unset
        if isinstance(_source_properties, Unset):
            source_properties = UNSET
        else:
            source_properties = UnstructuredDataBrowseSourceProperties.from_dict(_source_properties)

        unstructured_data_flr_browse_mount_model = cls(
            session_id=session_id,
            properties=properties,
            source_properties=source_properties,
        )

        unstructured_data_flr_browse_mount_model.additional_properties = d
        return unstructured_data_flr_browse_mount_model

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
