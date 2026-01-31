from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_platform_type import EPlatformType
from ..models.e_replica_state import EReplicaState
from ..models.e_replica_type import EReplicaType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RegularReplicaModel")


@_attrs_define
class RegularReplicaModel:
    """
    Attributes:
        id (UUID): ID of the replica.
        type_ (EReplicaType): Replica type.
        job_id (UUID): ID of the job that created the replica.
        name (str): Name of the job that created the replica.
        platform_name (EPlatformType): Platform type.
        creation_time (datetime.datetime): Date and time when the replica was created.
        state (EReplicaState): Replica state.
        policy_unique_id (str | Unset): Unique ID that identifies retention policy.
        platform_id (UUID | Unset): ID of the platform of the replica resource.
    """

    id: UUID
    type_: EReplicaType
    job_id: UUID
    name: str
    platform_name: EPlatformType
    creation_time: datetime.datetime
    state: EReplicaState
    policy_unique_id: str | Unset = UNSET
    platform_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        job_id = str(self.job_id)

        name = self.name

        platform_name = self.platform_name.value

        creation_time = self.creation_time.isoformat()

        state = self.state.value

        policy_unique_id = self.policy_unique_id

        platform_id: str | Unset = UNSET
        if not isinstance(self.platform_id, Unset):
            platform_id = str(self.platform_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "jobId": job_id,
                "name": name,
                "platformName": platform_name,
                "creationTime": creation_time,
                "state": state,
            }
        )
        if policy_unique_id is not UNSET:
            field_dict["policyUniqueId"] = policy_unique_id
        if platform_id is not UNSET:
            field_dict["platformId"] = platform_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EReplicaType(d.pop("type"))

        job_id = UUID(d.pop("jobId"))

        name = d.pop("name")

        platform_name = EPlatformType(d.pop("platformName"))

        creation_time = isoparse(d.pop("creationTime"))

        state = EReplicaState(d.pop("state"))

        policy_unique_id = d.pop("policyUniqueId", UNSET)

        _platform_id = d.pop("platformId", UNSET)
        platform_id: UUID | Unset
        if isinstance(_platform_id, Unset):
            platform_id = UNSET
        else:
            platform_id = UUID(_platform_id)

        regular_replica_model = cls(
            id=id,
            type_=type_,
            job_id=job_id,
            name=name,
            platform_name=platform_name,
            creation_time=creation_time,
            state=state,
            policy_unique_id=policy_unique_id,
            platform_id=platform_id,
        )

        regular_replica_model.additional_properties = d
        return regular_replica_model

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
