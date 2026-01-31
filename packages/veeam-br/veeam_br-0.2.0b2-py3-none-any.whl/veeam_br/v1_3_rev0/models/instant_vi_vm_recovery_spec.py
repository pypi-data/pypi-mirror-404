from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instant_vm_recovery_mode_type import EInstantVMRecoveryModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.secure_restore_spec import SecureRestoreSpec


T = TypeVar("T", bound="InstantViVMRecoverySpec")


@_attrs_define
class InstantViVMRecoverySpec:
    """Instant Recovery settings.

    Attributes:
        restore_point_id (UUID): ID of the restore point.
        type_ (EInstantVMRecoveryModeType): Restore mode.
        secure_restore (SecureRestoreSpec): Secure restore settings.
        vm_tags_restore_enabled (bool | Unset): If `true`, Veeam Backup & Replication restores tags that were assigned
            to the original VM, and assign them to the restored VM.
        nics_enabled (bool | Unset): If `true`, the restored VM is connected to the network.
        power_up (bool | Unset): If `true`, Veeam Backup & Replication powers on the restored VM on the target host.
        reason (str | Unset): Reason for restoring the VM.
        overwrite (bool | Unset): If `true`, the existing VM with the same name is overwritten.
    """

    restore_point_id: UUID
    type_: EInstantVMRecoveryModeType
    secure_restore: SecureRestoreSpec
    vm_tags_restore_enabled: bool | Unset = UNSET
    nics_enabled: bool | Unset = UNSET
    power_up: bool | Unset = UNSET
    reason: str | Unset = UNSET
    overwrite: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        secure_restore = self.secure_restore.to_dict()

        vm_tags_restore_enabled = self.vm_tags_restore_enabled

        nics_enabled = self.nics_enabled

        power_up = self.power_up

        reason = self.reason

        overwrite = self.overwrite

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
                "secureRestore": secure_restore,
            }
        )
        if vm_tags_restore_enabled is not UNSET:
            field_dict["vmTagsRestoreEnabled"] = vm_tags_restore_enabled
        if nics_enabled is not UNSET:
            field_dict["nicsEnabled"] = nics_enabled
        if power_up is not UNSET:
            field_dict["powerUp"] = power_up
        if reason is not UNSET:
            field_dict["reason"] = reason
        if overwrite is not UNSET:
            field_dict["overwrite"] = overwrite

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.secure_restore_spec import SecureRestoreSpec

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EInstantVMRecoveryModeType(d.pop("type"))

        secure_restore = SecureRestoreSpec.from_dict(d.pop("secureRestore"))

        vm_tags_restore_enabled = d.pop("vmTagsRestoreEnabled", UNSET)

        nics_enabled = d.pop("nicsEnabled", UNSET)

        power_up = d.pop("powerUp", UNSET)

        reason = d.pop("reason", UNSET)

        overwrite = d.pop("overwrite", UNSET)

        instant_vi_vm_recovery_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            secure_restore=secure_restore,
            vm_tags_restore_enabled=vm_tags_restore_enabled,
            nics_enabled=nics_enabled,
            power_up=power_up,
            reason=reason,
            overwrite=overwrite,
        )

        instant_vi_vm_recovery_spec.additional_properties = d
        return instant_vi_vm_recovery_spec

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
