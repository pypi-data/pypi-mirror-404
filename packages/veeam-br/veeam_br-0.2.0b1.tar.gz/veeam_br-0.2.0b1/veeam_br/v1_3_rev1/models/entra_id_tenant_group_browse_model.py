from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_entra_id_tenant_group_membership_type import EEntraIdTenantGroupMembershipType
from ..models.e_entra_id_tenant_group_type import EEntraIdTenantGroupType
from ..models.e_entra_id_tenant_item_type import EEntraIdTenantItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantGroupBrowseModel")


@_attrs_define
class EntraIdTenantGroupBrowseModel:
    """Microsoft Entra ID group.

    Attributes:
        id (UUID): Item ID.
        type_ (EEntraIdTenantItemType): Item type.
        display_name (str | Unset): Item display name.
        restore_point_id (UUID | Unset): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        restore_point_date (datetime.datetime | Unset): Restore point date and time.
        group_type (EEntraIdTenantGroupType | Unset): Group type.
        membership_type (EEntraIdTenantGroupMembershipType | Unset): Group membership type.
        description (str | Unset): Group description.
        archived (bool | Unset): If `true`, the group is archived.
        mail_enabled (bool | Unset): If `true`, the group is mail-enabled.
        visibility (str | Unset): Group visibility.
    """

    id: UUID
    type_: EEntraIdTenantItemType
    display_name: str | Unset = UNSET
    restore_point_id: UUID | Unset = UNSET
    restore_point_date: datetime.datetime | Unset = UNSET
    group_type: EEntraIdTenantGroupType | Unset = UNSET
    membership_type: EEntraIdTenantGroupMembershipType | Unset = UNSET
    description: str | Unset = UNSET
    archived: bool | Unset = UNSET
    mail_enabled: bool | Unset = UNSET
    visibility: str | Unset = UNSET
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

        group_type: str | Unset = UNSET
        if not isinstance(self.group_type, Unset):
            group_type = self.group_type.value

        membership_type: str | Unset = UNSET
        if not isinstance(self.membership_type, Unset):
            membership_type = self.membership_type.value

        description = self.description

        archived = self.archived

        mail_enabled = self.mail_enabled

        visibility = self.visibility

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
        if group_type is not UNSET:
            field_dict["groupType"] = group_type
        if membership_type is not UNSET:
            field_dict["membershipType"] = membership_type
        if description is not UNSET:
            field_dict["description"] = description
        if archived is not UNSET:
            field_dict["archived"] = archived
        if mail_enabled is not UNSET:
            field_dict["mailEnabled"] = mail_enabled
        if visibility is not UNSET:
            field_dict["visibility"] = visibility

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

        _group_type = d.pop("groupType", UNSET)
        group_type: EEntraIdTenantGroupType | Unset
        if isinstance(_group_type, Unset):
            group_type = UNSET
        else:
            group_type = EEntraIdTenantGroupType(_group_type)

        _membership_type = d.pop("membershipType", UNSET)
        membership_type: EEntraIdTenantGroupMembershipType | Unset
        if isinstance(_membership_type, Unset):
            membership_type = UNSET
        else:
            membership_type = EEntraIdTenantGroupMembershipType(_membership_type)

        description = d.pop("description", UNSET)

        archived = d.pop("archived", UNSET)

        mail_enabled = d.pop("mailEnabled", UNSET)

        visibility = d.pop("visibility", UNSET)

        entra_id_tenant_group_browse_model = cls(
            id=id,
            type_=type_,
            display_name=display_name,
            restore_point_id=restore_point_id,
            restore_point_date=restore_point_date,
            group_type=group_type,
            membership_type=membership_type,
            description=description,
            archived=archived,
            mail_enabled=mail_enabled,
            visibility=visibility,
        )

        entra_id_tenant_group_browse_model.additional_properties = d
        return entra_id_tenant_group_browse_model

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
