from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_post_backup_action import EPostBackupAction
from ..models.e_power_off_action import EPowerOffAction
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_policy_schedule_at_events_model import AgentBackupPolicyScheduleAtEventsModel
    from ..models.schedule_daily_model import ScheduleDailyModel


T = TypeVar("T", bound="WindowsAgentBackupPolicyWorkstationScheduleModel")


@_attrs_define
class WindowsAgentBackupPolicyWorkstationScheduleModel:
    """Schedule for the backup policy of Microsoft Windows workstations.

    Attributes:
        run_automatically (bool): If `true`, job scheduling is enabled. Default: False.
        daily (ScheduleDailyModel | Unset): Daily scheduling options.
        power_off_action (EPowerOffAction | Unset): Action that Veeam Agent for Microsoft Windows will perform when the
            protected computer is powered off at a time when the scheduled backup job must start.
        post_backup_action (EPostBackupAction | Unset): Action that Veeam Agent for Microsoft Windows will perform after
            the backup job completes successfully.
        at_events (AgentBackupPolicyScheduleAtEventsModel | Unset): Settings for backups scheduled at a particular
            event.
    """

    run_automatically: bool = False
    daily: ScheduleDailyModel | Unset = UNSET
    power_off_action: EPowerOffAction | Unset = UNSET
    post_backup_action: EPostBackupAction | Unset = UNSET
    at_events: AgentBackupPolicyScheduleAtEventsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_automatically = self.run_automatically

        daily: dict[str, Any] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        power_off_action: str | Unset = UNSET
        if not isinstance(self.power_off_action, Unset):
            power_off_action = self.power_off_action.value

        post_backup_action: str | Unset = UNSET
        if not isinstance(self.post_backup_action, Unset):
            post_backup_action = self.post_backup_action.value

        at_events: dict[str, Any] | Unset = UNSET
        if not isinstance(self.at_events, Unset):
            at_events = self.at_events.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runAutomatically": run_automatically,
            }
        )
        if daily is not UNSET:
            field_dict["daily"] = daily
        if power_off_action is not UNSET:
            field_dict["powerOffAction"] = power_off_action
        if post_backup_action is not UNSET:
            field_dict["postBackupAction"] = post_backup_action
        if at_events is not UNSET:
            field_dict["atEvents"] = at_events

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_policy_schedule_at_events_model import AgentBackupPolicyScheduleAtEventsModel
        from ..models.schedule_daily_model import ScheduleDailyModel

        d = dict(src_dict)
        run_automatically = d.pop("runAutomatically")

        _daily = d.pop("daily", UNSET)
        daily: ScheduleDailyModel | Unset
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        _power_off_action = d.pop("powerOffAction", UNSET)
        power_off_action: EPowerOffAction | Unset
        if isinstance(_power_off_action, Unset):
            power_off_action = UNSET
        else:
            power_off_action = EPowerOffAction(_power_off_action)

        _post_backup_action = d.pop("postBackupAction", UNSET)
        post_backup_action: EPostBackupAction | Unset
        if isinstance(_post_backup_action, Unset):
            post_backup_action = UNSET
        else:
            post_backup_action = EPostBackupAction(_post_backup_action)

        _at_events = d.pop("atEvents", UNSET)
        at_events: AgentBackupPolicyScheduleAtEventsModel | Unset
        if isinstance(_at_events, Unset):
            at_events = UNSET
        else:
            at_events = AgentBackupPolicyScheduleAtEventsModel.from_dict(_at_events)

        windows_agent_backup_policy_workstation_schedule_model = cls(
            run_automatically=run_automatically,
            daily=daily,
            power_off_action=power_off_action,
            post_backup_action=post_backup_action,
            at_events=at_events,
        )

        windows_agent_backup_policy_workstation_schedule_model.additional_properties = d
        return windows_agent_backup_policy_workstation_schedule_model

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
