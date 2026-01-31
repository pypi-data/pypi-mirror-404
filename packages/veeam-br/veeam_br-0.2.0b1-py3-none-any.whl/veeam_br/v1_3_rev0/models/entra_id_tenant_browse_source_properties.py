from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantBrowseSourceProperties")


@_attrs_define
class EntraIdTenantBrowseSourceProperties:
    """Properties of a Microsoft Entra ID tenant backup.

    Attributes:
        backup_id (UUID): ID of a Microsoft Entra ID tenant backup.
        tenant_id (UUID | Unset): Tenant ID assigned by Microsoft Entra ID.
        tenant_name (str | Unset): Microsoft Entra ID tenant name.
    """

    backup_id: UUID
    tenant_id: UUID | Unset = UNSET
    tenant_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_id = str(self.backup_id)

        tenant_id: str | Unset = UNSET
        if not isinstance(self.tenant_id, Unset):
            tenant_id = str(self.tenant_id)

        tenant_name = self.tenant_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backupId": backup_id,
            }
        )
        if tenant_id is not UNSET:
            field_dict["tenantId"] = tenant_id
        if tenant_name is not UNSET:
            field_dict["tenantName"] = tenant_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        backup_id = UUID(d.pop("backupId"))

        _tenant_id = d.pop("tenantId", UNSET)
        tenant_id: UUID | Unset
        if isinstance(_tenant_id, Unset):
            tenant_id = UNSET
        else:
            tenant_id = UUID(_tenant_id)

        tenant_name = d.pop("tenantName", UNSET)

        entra_id_tenant_browse_source_properties = cls(
            backup_id=backup_id,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
        )

        entra_id_tenant_browse_source_properties.additional_properties = d
        return entra_id_tenant_browse_source_properties

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
