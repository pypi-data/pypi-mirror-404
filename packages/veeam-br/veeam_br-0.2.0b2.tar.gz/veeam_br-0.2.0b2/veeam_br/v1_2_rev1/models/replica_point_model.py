from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_object_restore_point_operation import EObjectRestorePointOperation
from ..models.e_platform_type import EPlatformType
from ..models.e_replica_state import EReplicaState
from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="ReplicaPointModel")


@_attrs_define
class ReplicaPointModel:
    """Replica restore point.

    Attributes:
        id (UUID): ID of the restore point.
        name (str): Name of the object that the restore point was created for.
        platform_name (EPlatformType): Platform type.
        platform_id (UUID): ID of a platform where the object was created.
        creation_time (datetime.datetime): Date and time when the restore point was created.
        replica_id (UUID): ID of a replica that contains the restore point.
        allowed_operations (list[EObjectRestorePointOperation]): Array of operations allowed for the restore point.
        state (EReplicaState | Unset): Replica state.
        malware_status (ESuspiciousActivitySeverity | Unset): Malware status.
    """

    id: UUID
    name: str
    platform_name: EPlatformType
    platform_id: UUID
    creation_time: datetime.datetime
    replica_id: UUID
    allowed_operations: list[EObjectRestorePointOperation]
    state: EReplicaState | Unset = UNSET
    malware_status: ESuspiciousActivitySeverity | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        platform_name = self.platform_name.value

        platform_id = str(self.platform_id)

        creation_time = self.creation_time.isoformat()

        replica_id = str(self.replica_id)

        allowed_operations = []
        for allowed_operations_item_data in self.allowed_operations:
            allowed_operations_item = allowed_operations_item_data.value
            allowed_operations.append(allowed_operations_item)

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        malware_status: str | Unset = UNSET
        if not isinstance(self.malware_status, Unset):
            malware_status = self.malware_status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "platformName": platform_name,
                "platformId": platform_id,
                "creationTime": creation_time,
                "replicaId": replica_id,
                "allowedOperations": allowed_operations,
            }
        )
        if state is not UNSET:
            field_dict["state"] = state
        if malware_status is not UNSET:
            field_dict["malwareStatus"] = malware_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        platform_name = EPlatformType(d.pop("platformName"))

        platform_id = UUID(d.pop("platformId"))

        creation_time = isoparse(d.pop("creationTime"))

        replica_id = UUID(d.pop("replicaId"))

        allowed_operations = []
        _allowed_operations = d.pop("allowedOperations")
        for allowed_operations_item_data in _allowed_operations:
            allowed_operations_item = EObjectRestorePointOperation(allowed_operations_item_data)

            allowed_operations.append(allowed_operations_item)

        _state = d.pop("state", UNSET)
        state: EReplicaState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = EReplicaState(_state)

        _malware_status = d.pop("malwareStatus", UNSET)
        malware_status: ESuspiciousActivitySeverity | Unset
        if isinstance(_malware_status, Unset):
            malware_status = UNSET
        else:
            malware_status = ESuspiciousActivitySeverity(_malware_status)

        replica_point_model = cls(
            id=id,
            name=name,
            platform_name=platform_name,
            platform_id=platform_id,
            creation_time=creation_time,
            replica_id=replica_id,
            allowed_operations=allowed_operations,
            state=state,
            malware_status=malware_status,
        )

        replica_point_model.additional_properties = d
        return replica_point_model

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
