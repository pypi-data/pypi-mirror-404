from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_backup_copy_job_mode import EBackupCopyJobMode
from ..models.e_job_status import EJobStatus
from ..models.e_job_type import EJobType
from ..models.e_job_workload import EJobWorkload
from ..models.e_session_result import ESessionResult
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_after_job import RunAfterJob
    from ..models.session_progress_type_0 import SessionProgressType0


T = TypeVar("T", bound="JobStateModel")


@_attrs_define
class JobStateModel:
    """Job state.

    Attributes:
        id (UUID): Job ID.
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        status (EJobStatus): Current status of the job.
        last_result (ESessionResult): Result status.
        workload (EJobWorkload): Workload which the job must process.
        objects_count (int): Number of objects processed by the job.
        high_priority (bool): If `true`, the resource scheduler prioritized this job higher than other similar jobs and
            allocated resources to it in the first place.
        progress_percent (int): Progress percentage of the session.
        last_run (datetime.datetime | Unset): Date and time of the last run of the job.
        next_run (datetime.datetime | Unset): Date and time of the next run of the job.
        next_run_policy (str | Unset): Note in case the job is disabled, not scheduled, or configured to run after
            another job.
        repository_id (UUID | Unset): Backup repository ID.
        repository_name (str | Unset): Name of the backup repository.
        session_id (UUID | Unset): ID of the last job session.
        session_progress (None | SessionProgressType0 | Unset): Details on the progress of the session.
        run_after_job (RunAfterJob | Unset): Specifies that the job will run after another job.
        backup_copy_mode (EBackupCopyJobMode | Unset): Copy mode of backup copy job.
        is_storage_snapshot (bool | Unset): If `true`, the target for the job is snapshot storage.
    """

    id: UUID
    name: str
    type_: EJobType
    description: str
    status: EJobStatus
    last_result: ESessionResult
    workload: EJobWorkload
    objects_count: int
    high_priority: bool
    progress_percent: int
    last_run: datetime.datetime | Unset = UNSET
    next_run: datetime.datetime | Unset = UNSET
    next_run_policy: str | Unset = UNSET
    repository_id: UUID | Unset = UNSET
    repository_name: str | Unset = UNSET
    session_id: UUID | Unset = UNSET
    session_progress: None | SessionProgressType0 | Unset = UNSET
    run_after_job: RunAfterJob | Unset = UNSET
    backup_copy_mode: EBackupCopyJobMode | Unset = UNSET
    is_storage_snapshot: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.session_progress_type_0 import SessionProgressType0

        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        description = self.description

        status = self.status.value

        last_result = self.last_result.value

        workload = self.workload.value

        objects_count = self.objects_count

        high_priority = self.high_priority

        progress_percent = self.progress_percent

        last_run: str | Unset = UNSET
        if not isinstance(self.last_run, Unset):
            last_run = self.last_run.isoformat()

        next_run: str | Unset = UNSET
        if not isinstance(self.next_run, Unset):
            next_run = self.next_run.isoformat()

        next_run_policy = self.next_run_policy

        repository_id: str | Unset = UNSET
        if not isinstance(self.repository_id, Unset):
            repository_id = str(self.repository_id)

        repository_name = self.repository_name

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        session_progress: dict[str, Any] | None | Unset
        if isinstance(self.session_progress, Unset):
            session_progress = UNSET
        elif isinstance(self.session_progress, SessionProgressType0):
            session_progress = self.session_progress.to_dict()
        else:
            session_progress = self.session_progress

        run_after_job: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run_after_job, Unset):
            run_after_job = self.run_after_job.to_dict()

        backup_copy_mode: str | Unset = UNSET
        if not isinstance(self.backup_copy_mode, Unset):
            backup_copy_mode = self.backup_copy_mode.value

        is_storage_snapshot = self.is_storage_snapshot

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "description": description,
                "status": status,
                "lastResult": last_result,
                "workload": workload,
                "objectsCount": objects_count,
                "highPriority": high_priority,
                "progressPercent": progress_percent,
            }
        )
        if last_run is not UNSET:
            field_dict["lastRun"] = last_run
        if next_run is not UNSET:
            field_dict["nextRun"] = next_run
        if next_run_policy is not UNSET:
            field_dict["nextRunPolicy"] = next_run_policy
        if repository_id is not UNSET:
            field_dict["repositoryId"] = repository_id
        if repository_name is not UNSET:
            field_dict["repositoryName"] = repository_name
        if session_id is not UNSET:
            field_dict["sessionId"] = session_id
        if session_progress is not UNSET:
            field_dict["sessionProgress"] = session_progress
        if run_after_job is not UNSET:
            field_dict["runAfterJob"] = run_after_job
        if backup_copy_mode is not UNSET:
            field_dict["backupCopyMode"] = backup_copy_mode
        if is_storage_snapshot is not UNSET:
            field_dict["isStorageSnapshot"] = is_storage_snapshot

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_after_job import RunAfterJob
        from ..models.session_progress_type_0 import SessionProgressType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        status = EJobStatus(d.pop("status"))

        last_result = ESessionResult(d.pop("lastResult"))

        workload = EJobWorkload(d.pop("workload"))

        objects_count = d.pop("objectsCount")

        high_priority = d.pop("highPriority")

        progress_percent = d.pop("progressPercent")

        _last_run = d.pop("lastRun", UNSET)
        last_run: datetime.datetime | Unset
        if isinstance(_last_run, Unset):
            last_run = UNSET
        else:
            last_run = isoparse(_last_run)

        _next_run = d.pop("nextRun", UNSET)
        next_run: datetime.datetime | Unset
        if isinstance(_next_run, Unset):
            next_run = UNSET
        else:
            next_run = isoparse(_next_run)

        next_run_policy = d.pop("nextRunPolicy", UNSET)

        _repository_id = d.pop("repositoryId", UNSET)
        repository_id: UUID | Unset
        if isinstance(_repository_id, Unset):
            repository_id = UNSET
        else:
            repository_id = UUID(_repository_id)

        repository_name = d.pop("repositoryName", UNSET)

        _session_id = d.pop("sessionId", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        def _parse_session_progress(data: object) -> None | SessionProgressType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_session_progress_type_0 = SessionProgressType0.from_dict(data)

                return componentsschemas_session_progress_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SessionProgressType0 | Unset, data)

        session_progress = _parse_session_progress(d.pop("sessionProgress", UNSET))

        _run_after_job = d.pop("runAfterJob", UNSET)
        run_after_job: RunAfterJob | Unset
        if isinstance(_run_after_job, Unset):
            run_after_job = UNSET
        else:
            run_after_job = RunAfterJob.from_dict(_run_after_job)

        _backup_copy_mode = d.pop("backupCopyMode", UNSET)
        backup_copy_mode: EBackupCopyJobMode | Unset
        if isinstance(_backup_copy_mode, Unset):
            backup_copy_mode = UNSET
        else:
            backup_copy_mode = EBackupCopyJobMode(_backup_copy_mode)

        is_storage_snapshot = d.pop("isStorageSnapshot", UNSET)

        job_state_model = cls(
            id=id,
            name=name,
            type_=type_,
            description=description,
            status=status,
            last_result=last_result,
            workload=workload,
            objects_count=objects_count,
            high_priority=high_priority,
            progress_percent=progress_percent,
            last_run=last_run,
            next_run=next_run,
            next_run_policy=next_run_policy,
            repository_id=repository_id,
            repository_name=repository_name,
            session_id=session_id,
            session_progress=session_progress,
            run_after_job=run_after_job,
            backup_copy_mode=backup_copy_mode,
            is_storage_snapshot=is_storage_snapshot,
        )

        job_state_model.additional_properties = d
        return job_state_model

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
