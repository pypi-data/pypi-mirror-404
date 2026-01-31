from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_platform_type import EPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupModel")


@_attrs_define
class BackupModel:
    """
    Attributes:
        id (UUID): Backup ID.
        name (str): Name of the job that created the backup.
        platform_name (EPlatformType): Platform type.
        platform_id (UUID): ID of the platform of the backup resource.
        creation_time (datetime.datetime): Date and time when the backup was created.
        repository_id (UUID): ID of the backup repository where the backup is stored.
        job_id (UUID | Unset): ID of the job that created the backup.
        policy_unique_id (str | Unset): Unique ID that identifies retention policy.
    """

    id: UUID
    name: str
    platform_name: EPlatformType
    platform_id: UUID
    creation_time: datetime.datetime
    repository_id: UUID
    job_id: UUID | Unset = UNSET
    policy_unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        platform_name = self.platform_name.value

        platform_id = str(self.platform_id)

        creation_time = self.creation_time.isoformat()

        repository_id = str(self.repository_id)

        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        policy_unique_id = self.policy_unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "platformName": platform_name,
                "platformId": platform_id,
                "creationTime": creation_time,
                "repositoryId": repository_id,
            }
        )
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if policy_unique_id is not UNSET:
            field_dict["policyUniqueId"] = policy_unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        platform_name = EPlatformType(d.pop("platformName"))

        platform_id = UUID(d.pop("platformId"))

        creation_time = isoparse(d.pop("creationTime"))

        repository_id = UUID(d.pop("repositoryId"))

        _job_id = d.pop("jobId", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id, Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)

        policy_unique_id = d.pop("policyUniqueId", UNSET)

        backup_model = cls(
            id=id,
            name=name,
            platform_name=platform_name,
            platform_id=platform_id,
            creation_time=creation_time,
            repository_id=repository_id,
            job_id=job_id,
            policy_unique_id=policy_unique_id,
        )

        backup_model.additional_properties = d
        return backup_model

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
