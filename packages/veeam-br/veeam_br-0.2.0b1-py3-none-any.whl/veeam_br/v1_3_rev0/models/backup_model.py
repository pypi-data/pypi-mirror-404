from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_job_type import EJobType
from ..models.e_platform_type import EPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupModel")


@_attrs_define
class BackupModel:
    """Backup.

    Attributes:
        id (UUID): Backup ID.
        name (str): Name of the job that created the backup.
        platform_name (EPlatformType): Platform type.
        platform_id (UUID): ID of the platform of the backup resource.
        creation_time (datetime.datetime): Date and time when the backup was created.
        repository_id (UUID): ID of the backup repository where the backup is stored.
        job_type (EJobType): Type of the job.
        job_id (UUID | Unset): ID of the job that created the backup.
        policy_unique_id (str | Unset): Unique ID that identifies retention policy.
        repository_name (str | Unset): Name of the backup repository where the backup is stored.
    """

    id: UUID
    name: str
    platform_name: EPlatformType
    platform_id: UUID
    creation_time: datetime.datetime
    repository_id: UUID
    job_type: EJobType
    job_id: UUID | Unset = UNSET
    policy_unique_id: str | Unset = UNSET
    repository_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        platform_name = self.platform_name.value

        platform_id = str(self.platform_id)

        creation_time = self.creation_time.isoformat()

        repository_id = str(self.repository_id)

        job_type = self.job_type.value

        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        policy_unique_id = self.policy_unique_id

        repository_name = self.repository_name

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
                "jobType": job_type,
            }
        )
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if policy_unique_id is not UNSET:
            field_dict["policyUniqueId"] = policy_unique_id
        if repository_name is not UNSET:
            field_dict["repositoryName"] = repository_name

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

        job_type = EJobType(d.pop("jobType"))

        _job_id = d.pop("jobId", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id, Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)

        policy_unique_id = d.pop("policyUniqueId", UNSET)

        repository_name = d.pop("repositoryName", UNSET)

        backup_model = cls(
            id=id,
            name=name,
            platform_name=platform_name,
            platform_id=platform_id,
            creation_time=creation_time,
            repository_id=repository_id,
            job_type=job_type,
            job_id=job_id,
            policy_unique_id=policy_unique_id,
            repository_name=repository_name,
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
