from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_browse_source_properties import EntraIdTenantBrowseSourceProperties


T = TypeVar("T", bound="EntraIdTenantBrowseMountModel")


@_attrs_define
class EntraIdTenantBrowseMountModel:
    """Mount point.

    Attributes:
        session_id (UUID): Mount session ID.
        source_properties (EntraIdTenantBrowseSourceProperties | Unset): Properties of a Microsoft Entra ID tenant
            backup.
    """

    session_id: UUID
    source_properties: EntraIdTenantBrowseSourceProperties | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = str(self.session_id)

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
        if source_properties is not UNSET:
            field_dict["sourceProperties"] = source_properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_browse_source_properties import EntraIdTenantBrowseSourceProperties

        d = dict(src_dict)
        session_id = UUID(d.pop("sessionId"))

        _source_properties = d.pop("sourceProperties", UNSET)
        source_properties: EntraIdTenantBrowseSourceProperties | Unset
        if isinstance(_source_properties, Unset):
            source_properties = UNSET
        else:
            source_properties = EntraIdTenantBrowseSourceProperties.from_dict(_source_properties)

        entra_id_tenant_browse_mount_model = cls(
            session_id=session_id,
            source_properties=source_properties,
        )

        entra_id_tenant_browse_mount_model.additional_properties = d
        return entra_id_tenant_browse_mount_model

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
