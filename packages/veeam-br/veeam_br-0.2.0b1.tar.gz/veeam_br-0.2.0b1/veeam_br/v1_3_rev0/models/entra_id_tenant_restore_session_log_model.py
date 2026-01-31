from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_entra_id_tenant_restore_session_log_status import EEntraIdTenantRestoreSessionLogStatus
from ..models.e_entra_id_tenant_restore_session_log_style import EEntraIdTenantRestoreSessionLogStyle
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreSessionLogModel")


@_attrs_define
class EntraIdTenantRestoreSessionLogModel:
    """Restore session log record.

    Attributes:
        id (UUID): Record ID.
        title (str): Event title.
        description (str): Event description.
        start_time (datetime.datetime): Date and time when the event was started.
        status (EEntraIdTenantRestoreSessionLogStatus): Event status.
        style (EEntraIdTenantRestoreSessionLogStyle): Font style of the log record.
        update_time (datetime.datetime | Unset): Date and time when the event was updated.
    """

    id: UUID
    title: str
    description: str
    start_time: datetime.datetime
    status: EEntraIdTenantRestoreSessionLogStatus
    style: EEntraIdTenantRestoreSessionLogStyle
    update_time: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        title = self.title

        description = self.description

        start_time = self.start_time.isoformat()

        status = self.status.value

        style = self.style.value

        update_time: str | Unset = UNSET
        if not isinstance(self.update_time, Unset):
            update_time = self.update_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "description": description,
                "startTime": start_time,
                "status": status,
                "style": style,
            }
        )
        if update_time is not UNSET:
            field_dict["updateTime"] = update_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        title = d.pop("title")

        description = d.pop("description")

        start_time = isoparse(d.pop("startTime"))

        status = EEntraIdTenantRestoreSessionLogStatus(d.pop("status"))

        style = EEntraIdTenantRestoreSessionLogStyle(d.pop("style"))

        _update_time = d.pop("updateTime", UNSET)
        update_time: datetime.datetime | Unset
        if isinstance(_update_time, Unset):
            update_time = UNSET
        else:
            update_time = isoparse(_update_time)

        entra_id_tenant_restore_session_log_model = cls(
            id=id,
            title=title,
            description=description,
            start_time=start_time,
            status=status,
            style=style,
            update_time=update_time,
        )

        entra_id_tenant_restore_session_log_model.additional_properties = d
        return entra_id_tenant_restore_session_log_model

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
