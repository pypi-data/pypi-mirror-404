from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRoleBrowseModel")


@_attrs_define
class EntraIdTenantRoleBrowseModel:
    """Microsoft Entra ID roles.

    Attributes:
        id (UUID): Item ID.
        restore_point_id (UUID): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        restore_point_date (datetime.datetime): Restore point date and time.
        type_ (EEntraIdTenantItemType): Item type.
        is_built_in (bool): If `true`, the role is built-in.
        is_enabled (bool): If `true`, the role is enabled.
        display_name (str | Unset): Item display name.
        description (str | Unset): Role description.
    """

    id: UUID
    restore_point_id: UUID
    restore_point_date: datetime.datetime
    type_: EEntraIdTenantItemType
    is_built_in: bool
    is_enabled: bool
    display_name: str | Unset = UNSET
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        restore_point_id = str(self.restore_point_id)

        restore_point_date = self.restore_point_date.isoformat()

        type_ = self.type_.value

        is_built_in = self.is_built_in

        is_enabled = self.is_enabled

        display_name = self.display_name

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "restorePointId": restore_point_id,
                "restorePointDate": restore_point_date,
                "type": type_,
                "isBuiltIn": is_built_in,
                "isEnabled": is_enabled,
            }
        )
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        restore_point_id = UUID(d.pop("restorePointId"))

        restore_point_date = isoparse(d.pop("restorePointDate"))

        type_ = EEntraIdTenantItemType(d.pop("type"))

        is_built_in = d.pop("isBuiltIn")

        is_enabled = d.pop("isEnabled")

        display_name = d.pop("displayName", UNSET)

        description = d.pop("description", UNSET)

        entra_id_tenant_role_browse_model = cls(
            id=id,
            restore_point_id=restore_point_id,
            restore_point_date=restore_point_date,
            type_=type_,
            is_built_in=is_built_in,
            is_enabled=is_enabled,
            display_name=display_name,
            description=description,
        )

        entra_id_tenant_role_browse_model.additional_properties = d
        return entra_id_tenant_role_browse_model

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
