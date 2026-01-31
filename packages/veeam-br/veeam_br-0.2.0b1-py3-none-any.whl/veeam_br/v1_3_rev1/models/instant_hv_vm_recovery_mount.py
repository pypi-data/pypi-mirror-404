from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_instant_recovery_mount_state import EInstantRecoveryMountState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.instant_hv_vm_recovery_spec import InstantHvVMRecoverySpec


T = TypeVar("T", bound="InstantHvVMRecoveryMount")


@_attrs_define
class InstantHvVMRecoveryMount:
    """VM mount point.

    Attributes:
        id (UUID): Mount point ID.
        session_id (UUID): Restore session ID. Use the ID to track the progress. For details, see [Get
            Session](Sessions#operation/GetSession).
        state (EInstantRecoveryMountState): Mount state.
        spec (InstantHvVMRecoverySpec): Instant Recovery settings.
        vm_name (str): Name of the recovered VM.
        job_name (str): Name of the Backup job.
        restore_point_date (datetime.datetime): Date and time when the restore point was created.
        host_name (str | Unset): Name of the destination host.
        error_message (str | Unset): Error message.
    """

    id: UUID
    session_id: UUID
    state: EInstantRecoveryMountState
    spec: InstantHvVMRecoverySpec
    vm_name: str
    job_name: str
    restore_point_date: datetime.datetime
    host_name: str | Unset = UNSET
    error_message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        session_id = str(self.session_id)

        state = self.state.value

        spec = self.spec.to_dict()

        vm_name = self.vm_name

        job_name = self.job_name

        restore_point_date = self.restore_point_date.isoformat()

        host_name = self.host_name

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sessionId": session_id,
                "state": state,
                "spec": spec,
                "vmName": vm_name,
                "jobName": job_name,
                "restorePointDate": restore_point_date,
            }
        )
        if host_name is not UNSET:
            field_dict["hostName"] = host_name
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.instant_hv_vm_recovery_spec import InstantHvVMRecoverySpec

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        session_id = UUID(d.pop("sessionId"))

        state = EInstantRecoveryMountState(d.pop("state"))

        spec = InstantHvVMRecoverySpec.from_dict(d.pop("spec"))

        vm_name = d.pop("vmName")

        job_name = d.pop("jobName")

        restore_point_date = isoparse(d.pop("restorePointDate"))

        host_name = d.pop("hostName", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        instant_hv_vm_recovery_mount = cls(
            id=id,
            session_id=session_id,
            state=state,
            spec=spec,
            vm_name=vm_name,
            job_name=job_name,
            restore_point_date=restore_point_date,
            host_name=host_name,
            error_message=error_message,
        )

        instant_hv_vm_recovery_mount.additional_properties = d
        return instant_hv_vm_recovery_mount

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
