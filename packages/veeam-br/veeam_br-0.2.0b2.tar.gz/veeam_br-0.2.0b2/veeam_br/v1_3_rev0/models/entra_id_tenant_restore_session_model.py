from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_entra_id_tenant_restore_session_state import EEntraIdTenantRestoreSessionState
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreSessionModel")


@_attrs_define
class EntraIdTenantRestoreSessionModel:
    """Restore session of a Microsoft Entra ID tenant.

    Attributes:
        id (UUID): Restore session ID.
        name (str): Restore session name.
        state (EEntraIdTenantRestoreSessionState): Session state.
        creation_time (datetime.datetime | Unset): Date and time when the session was created.
        end_time (datetime.datetime | Unset): Date and time when the session was stopped.
        reason (str | Unset): Reason for restoring Microsoft Entra ID items.
        parent_session_id (UUID | Unset): Mount session ID.
    """

    id: UUID
    name: str
    state: EEntraIdTenantRestoreSessionState
    creation_time: datetime.datetime | Unset = UNSET
    end_time: datetime.datetime | Unset = UNSET
    reason: str | Unset = UNSET
    parent_session_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        state = self.state.value

        creation_time: str | Unset = UNSET
        if not isinstance(self.creation_time, Unset):
            creation_time = self.creation_time.isoformat()

        end_time: str | Unset = UNSET
        if not isinstance(self.end_time, Unset):
            end_time = self.end_time.isoformat()

        reason = self.reason

        parent_session_id: str | Unset = UNSET
        if not isinstance(self.parent_session_id, Unset):
            parent_session_id = str(self.parent_session_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "state": state,
            }
        )
        if creation_time is not UNSET:
            field_dict["creationTime"] = creation_time
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if reason is not UNSET:
            field_dict["reason"] = reason
        if parent_session_id is not UNSET:
            field_dict["parentSessionId"] = parent_session_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        state = EEntraIdTenantRestoreSessionState(d.pop("state"))

        _creation_time = d.pop("creationTime", UNSET)
        creation_time: datetime.datetime | Unset
        if isinstance(_creation_time, Unset):
            creation_time = UNSET
        else:
            creation_time = isoparse(_creation_time)

        _end_time = d.pop("endTime", UNSET)
        end_time: datetime.datetime | Unset
        if isinstance(_end_time, Unset):
            end_time = UNSET
        else:
            end_time = isoparse(_end_time)

        reason = d.pop("reason", UNSET)

        _parent_session_id = d.pop("parentSessionId", UNSET)
        parent_session_id: UUID | Unset
        if isinstance(_parent_session_id, Unset):
            parent_session_id = UNSET
        else:
            parent_session_id = UUID(_parent_session_id)

        entra_id_tenant_restore_session_model = cls(
            id=id,
            name=name,
            state=state,
            creation_time=creation_time,
            end_time=end_time,
            reason=reason,
            parent_session_id=parent_session_id,
        )

        entra_id_tenant_restore_session_model.additional_properties = d
        return entra_id_tenant_restore_session_model

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
