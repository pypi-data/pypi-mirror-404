from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_entra_id_tenant_application_type import EEntraIdTenantApplicationType
from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantApplicationBrowseModel")


@_attrs_define
class EntraIdTenantApplicationBrowseModel:
    """Application used to add the tenant.

    Attributes:
        id (UUID): Item ID.
        type_ (EEntraIdTenantItemType): Item type.
        display_name (str | Unset): Item display name.
        restore_point_id (UUID | Unset): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        restore_point_date (datetime.datetime | Unset): Restore point date and time.
        application_type (EEntraIdTenantApplicationType | Unset): Application type.
        enabled (bool | Unset): If `true`, the application is enabled.
        tags (list[str] | Unset): Array of application tags.
        description (str | Unset): Application description.
    """

    id: UUID
    type_: EEntraIdTenantItemType
    display_name: str | Unset = UNSET
    restore_point_id: UUID | Unset = UNSET
    restore_point_date: datetime.datetime | Unset = UNSET
    application_type: EEntraIdTenantApplicationType | Unset = UNSET
    enabled: bool | Unset = UNSET
    tags: list[str] | Unset = UNSET
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        display_name = self.display_name

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        restore_point_date: str | Unset = UNSET
        if not isinstance(self.restore_point_date, Unset):
            restore_point_date = self.restore_point_date.isoformat()

        application_type: str | Unset = UNSET
        if not isinstance(self.application_type, Unset):
            application_type = self.application_type.value

        enabled = self.enabled

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id
        if restore_point_date is not UNSET:
            field_dict["restorePointDate"] = restore_point_date
        if application_type is not UNSET:
            field_dict["applicationType"] = application_type
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if tags is not UNSET:
            field_dict["tags"] = tags
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EEntraIdTenantItemType(d.pop("type"))

        display_name = d.pop("displayName", UNSET)

        _restore_point_id = d.pop("restorePointId", UNSET)
        restore_point_id: UUID | Unset
        if isinstance(_restore_point_id, Unset):
            restore_point_id = UNSET
        else:
            restore_point_id = UUID(_restore_point_id)

        _restore_point_date = d.pop("restorePointDate", UNSET)
        restore_point_date: datetime.datetime | Unset
        if isinstance(_restore_point_date, Unset):
            restore_point_date = UNSET
        else:
            restore_point_date = isoparse(_restore_point_date)

        _application_type = d.pop("applicationType", UNSET)
        application_type: EEntraIdTenantApplicationType | Unset
        if isinstance(_application_type, Unset):
            application_type = UNSET
        else:
            application_type = EEntraIdTenantApplicationType(_application_type)

        enabled = d.pop("enabled", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        description = d.pop("description", UNSET)

        entra_id_tenant_application_browse_model = cls(
            id=id,
            type_=type_,
            display_name=display_name,
            restore_point_id=restore_point_id,
            restore_point_date=restore_point_date,
            application_type=application_type,
            enabled=enabled,
            tags=tags,
            description=description,
        )

        entra_id_tenant_application_browse_model.additional_properties = d
        return entra_id_tenant_application_browse_model

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
