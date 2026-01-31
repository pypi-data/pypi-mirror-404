from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_type import EFlrType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_browse_properties import FlrBrowseProperties
    from ..models.flr_browse_source_properties import FlrBrowseSourceProperties


T = TypeVar("T", bound="FlrBrowseMountModel")


@_attrs_define
class FlrBrowseMountModel:
    """File restore mount points.

    Attributes:
        session_id (UUID): Restore session ID.
        type_ (EFlrType): Restore type.
        source_properties (FlrBrowseSourceProperties): Restore point settings.
        properties (FlrBrowseProperties | Unset): Browser properties.
    """

    session_id: UUID
    type_: EFlrType
    source_properties: FlrBrowseSourceProperties
    properties: FlrBrowseProperties | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = str(self.session_id)

        type_ = self.type_.value

        source_properties = self.source_properties.to_dict()

        properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.properties, Unset):
            properties = self.properties.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sessionId": session_id,
                "type": type_,
                "sourceProperties": source_properties,
            }
        )
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_browse_properties import FlrBrowseProperties
        from ..models.flr_browse_source_properties import FlrBrowseSourceProperties

        d = dict(src_dict)
        session_id = UUID(d.pop("sessionId"))

        type_ = EFlrType(d.pop("type"))

        source_properties = FlrBrowseSourceProperties.from_dict(d.pop("sourceProperties"))

        _properties = d.pop("properties", UNSET)
        properties: FlrBrowseProperties | Unset
        if isinstance(_properties, Unset):
            properties = UNSET
        else:
            properties = FlrBrowseProperties.from_dict(_properties)

        flr_browse_mount_model = cls(
            session_id=session_id,
            type_=type_,
            source_properties=source_properties,
            properties=properties,
        )

        flr_browse_mount_model.additional_properties = d
        return flr_browse_mount_model

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
