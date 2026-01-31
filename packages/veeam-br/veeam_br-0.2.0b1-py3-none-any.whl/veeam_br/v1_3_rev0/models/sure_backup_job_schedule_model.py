from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_after_this_job_model import ScheduleAfterThisJobModel
    from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
    from ..models.schedule_daily_model import ScheduleDailyModel
    from ..models.schedule_monthly_model import ScheduleMonthlyModel
    from ..models.schedule_periodically_model import SchedulePeriodicallyModel


T = TypeVar("T", bound="SureBackupJobScheduleModel")


@_attrs_define
class SureBackupJobScheduleModel:
    """SureBackup job schedule.

    Attributes:
        run_automatically (bool | Unset): If `true`, job scheduling is enabled. Default: False.
        daily (ScheduleDailyModel | Unset): Daily scheduling options.
        monthly (ScheduleMonthlyModel | Unset): Monthly scheduling options.
        periodically (SchedulePeriodicallyModel | Unset): Periodic scheduling options.
        continuously (ScheduleBackupWindowModel | Unset): Backup window settings.
        after_this_job (ScheduleAfterThisJobModel | Unset): Job chaining options.
        wait_for_linked_jobs (bool | Unset): If `true`, the SureBackup job will wait for linked jobs to finish.
        wait_time_minutes (int | Unset): Number of minutes that the SureBackup job will wait for linked jobs to finish.
    """

    run_automatically: bool | Unset = False
    daily: ScheduleDailyModel | Unset = UNSET
    monthly: ScheduleMonthlyModel | Unset = UNSET
    periodically: SchedulePeriodicallyModel | Unset = UNSET
    continuously: ScheduleBackupWindowModel | Unset = UNSET
    after_this_job: ScheduleAfterThisJobModel | Unset = UNSET
    wait_for_linked_jobs: bool | Unset = UNSET
    wait_time_minutes: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_automatically = self.run_automatically

        daily: dict[str, Any] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        monthly: dict[str, Any] | Unset = UNSET
        if not isinstance(self.monthly, Unset):
            monthly = self.monthly.to_dict()

        periodically: dict[str, Any] | Unset = UNSET
        if not isinstance(self.periodically, Unset):
            periodically = self.periodically.to_dict()

        continuously: dict[str, Any] | Unset = UNSET
        if not isinstance(self.continuously, Unset):
            continuously = self.continuously.to_dict()

        after_this_job: dict[str, Any] | Unset = UNSET
        if not isinstance(self.after_this_job, Unset):
            after_this_job = self.after_this_job.to_dict()

        wait_for_linked_jobs = self.wait_for_linked_jobs

        wait_time_minutes = self.wait_time_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if run_automatically is not UNSET:
            field_dict["runAutomatically"] = run_automatically
        if daily is not UNSET:
            field_dict["daily"] = daily
        if monthly is not UNSET:
            field_dict["monthly"] = monthly
        if periodically is not UNSET:
            field_dict["periodically"] = periodically
        if continuously is not UNSET:
            field_dict["continuously"] = continuously
        if after_this_job is not UNSET:
            field_dict["afterThisJob"] = after_this_job
        if wait_for_linked_jobs is not UNSET:
            field_dict["waitForLinkedJobs"] = wait_for_linked_jobs
        if wait_time_minutes is not UNSET:
            field_dict["waitTimeMinutes"] = wait_time_minutes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_after_this_job_model import ScheduleAfterThisJobModel
        from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
        from ..models.schedule_daily_model import ScheduleDailyModel
        from ..models.schedule_monthly_model import ScheduleMonthlyModel
        from ..models.schedule_periodically_model import SchedulePeriodicallyModel

        d = dict(src_dict)
        run_automatically = d.pop("runAutomatically", UNSET)

        _daily = d.pop("daily", UNSET)
        daily: ScheduleDailyModel | Unset
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        _monthly = d.pop("monthly", UNSET)
        monthly: ScheduleMonthlyModel | Unset
        if isinstance(_monthly, Unset):
            monthly = UNSET
        else:
            monthly = ScheduleMonthlyModel.from_dict(_monthly)

        _periodically = d.pop("periodically", UNSET)
        periodically: SchedulePeriodicallyModel | Unset
        if isinstance(_periodically, Unset):
            periodically = UNSET
        else:
            periodically = SchedulePeriodicallyModel.from_dict(_periodically)

        _continuously = d.pop("continuously", UNSET)
        continuously: ScheduleBackupWindowModel | Unset
        if isinstance(_continuously, Unset):
            continuously = UNSET
        else:
            continuously = ScheduleBackupWindowModel.from_dict(_continuously)

        _after_this_job = d.pop("afterThisJob", UNSET)
        after_this_job: ScheduleAfterThisJobModel | Unset
        if isinstance(_after_this_job, Unset):
            after_this_job = UNSET
        else:
            after_this_job = ScheduleAfterThisJobModel.from_dict(_after_this_job)

        wait_for_linked_jobs = d.pop("waitForLinkedJobs", UNSET)

        wait_time_minutes = d.pop("waitTimeMinutes", UNSET)

        sure_backup_job_schedule_model = cls(
            run_automatically=run_automatically,
            daily=daily,
            monthly=monthly,
            periodically=periodically,
            continuously=continuously,
            after_this_job=after_this_job,
            wait_for_linked_jobs=wait_for_linked_jobs,
            wait_time_minutes=wait_time_minutes,
        )

        sure_backup_job_schedule_model.additional_properties = d
        return sure_backup_job_schedule_model

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
