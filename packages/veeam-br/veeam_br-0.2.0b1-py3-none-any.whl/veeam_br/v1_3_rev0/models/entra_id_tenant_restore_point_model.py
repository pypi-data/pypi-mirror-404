from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="EntraIdTenantRestorePointModel")


@_attrs_define
class EntraIdTenantRestorePointModel:
    """Microsoft Entra ID restore point.

    Attributes:
        id (UUID): Restore point ID.
        creation_time (datetime.datetime): Date and time when the restore point was created.
    """

    id: UUID
    creation_time: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        creation_time = self.creation_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "creationTime": creation_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        creation_time = isoparse(d.pop("creationTime"))

        entra_id_tenant_restore_point_model = cls(
            id=id,
            creation_time=creation_time,
        )

        entra_id_tenant_restore_point_model.additional_properties = d
        return entra_id_tenant_restore_point_model

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
