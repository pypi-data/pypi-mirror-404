from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_policy_backup_timeout_model import AgentBackupPolicyBackupTimeoutModel


T = TypeVar("T", bound="AgentBackupPolicyScheduleAtEventsModel")


@_attrs_define
class AgentBackupPolicyScheduleAtEventsModel:
    """Settings for backups scheduled at a particular event.

    Attributes:
        backup_at_lock (bool | Unset): If `true`, Veeam Agent backup job will start when the user locks the protected
            computer.
        backup_at_logoff (bool | Unset): If `true`, Veeam Agent backup job will start when the user working with the
            protected computer performs a logout operation.
        backup_at_storage_attach (bool | Unset): If `true`, Veeam Agent backup job will start when the backup storage
            becomes available.
        eject_storage_after_backup (bool | Unset): If `true`, Veeam Agent for Microsoft Windows will unmount the storage
            device after the backup job completes successfully.
        backup_timeout (AgentBackupPolicyBackupTimeoutModel | Unset): Interval between the backup job sessions.
    """

    backup_at_lock: bool | Unset = UNSET
    backup_at_logoff: bool | Unset = UNSET
    backup_at_storage_attach: bool | Unset = UNSET
    eject_storage_after_backup: bool | Unset = UNSET
    backup_timeout: AgentBackupPolicyBackupTimeoutModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_at_lock = self.backup_at_lock

        backup_at_logoff = self.backup_at_logoff

        backup_at_storage_attach = self.backup_at_storage_attach

        eject_storage_after_backup = self.eject_storage_after_backup

        backup_timeout: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backup_timeout, Unset):
            backup_timeout = self.backup_timeout.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_at_lock is not UNSET:
            field_dict["backupAtLock"] = backup_at_lock
        if backup_at_logoff is not UNSET:
            field_dict["backupAtLogoff"] = backup_at_logoff
        if backup_at_storage_attach is not UNSET:
            field_dict["backupAtStorageAttach"] = backup_at_storage_attach
        if eject_storage_after_backup is not UNSET:
            field_dict["ejectStorageAfterBackup"] = eject_storage_after_backup
        if backup_timeout is not UNSET:
            field_dict["backupTimeout"] = backup_timeout

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_policy_backup_timeout_model import AgentBackupPolicyBackupTimeoutModel

        d = dict(src_dict)
        backup_at_lock = d.pop("backupAtLock", UNSET)

        backup_at_logoff = d.pop("backupAtLogoff", UNSET)

        backup_at_storage_attach = d.pop("backupAtStorageAttach", UNSET)

        eject_storage_after_backup = d.pop("ejectStorageAfterBackup", UNSET)

        _backup_timeout = d.pop("backupTimeout", UNSET)
        backup_timeout: AgentBackupPolicyBackupTimeoutModel | Unset
        if isinstance(_backup_timeout, Unset):
            backup_timeout = UNSET
        else:
            backup_timeout = AgentBackupPolicyBackupTimeoutModel.from_dict(_backup_timeout)

        agent_backup_policy_schedule_at_events_model = cls(
            backup_at_lock=backup_at_lock,
            backup_at_logoff=backup_at_logoff,
            backup_at_storage_attach=backup_at_storage_attach,
            eject_storage_after_backup=eject_storage_after_backup,
            backup_timeout=backup_timeout,
        )

        agent_backup_policy_schedule_at_events_model.additional_properties = d
        return agent_backup_policy_schedule_at_events_model

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
