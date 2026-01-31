from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hyper_v_guest_quiescence_settings_model import HyperVGuestQuiescenceSettingsModel


T = TypeVar("T", bound="BackupJobAdvancedSettingsHyperVModel")


@_attrs_define
class BackupJobAdvancedSettingsHyperVModel:
    """Microsoft Hyper-V settings for the job.

    Attributes:
        guest_quiescence (HyperVGuestQuiescenceSettingsModel | Unset): Microsoft Microsoft Hyper-V guest quiescence
            settings.
        changed_block_tracking (bool | Unset): If `true`, changed block tracking (CBT) is enabled for fast incremental
            backup and replication of protected VMs.
        volume_snapshots (bool | Unset): If `true`, allow processing of multiple VMs with a single volume snapshot.
    """

    guest_quiescence: HyperVGuestQuiescenceSettingsModel | Unset = UNSET
    changed_block_tracking: bool | Unset = UNSET
    volume_snapshots: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        guest_quiescence: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_quiescence, Unset):
            guest_quiescence = self.guest_quiescence.to_dict()

        changed_block_tracking = self.changed_block_tracking

        volume_snapshots = self.volume_snapshots

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if guest_quiescence is not UNSET:
            field_dict["guestQuiescence"] = guest_quiescence
        if changed_block_tracking is not UNSET:
            field_dict["changedBlockTracking"] = changed_block_tracking
        if volume_snapshots is not UNSET:
            field_dict["volumeSnapshots"] = volume_snapshots

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_guest_quiescence_settings_model import HyperVGuestQuiescenceSettingsModel

        d = dict(src_dict)
        _guest_quiescence = d.pop("guestQuiescence", UNSET)
        guest_quiescence: HyperVGuestQuiescenceSettingsModel | Unset
        if isinstance(_guest_quiescence, Unset):
            guest_quiescence = UNSET
        else:
            guest_quiescence = HyperVGuestQuiescenceSettingsModel.from_dict(_guest_quiescence)

        changed_block_tracking = d.pop("changedBlockTracking", UNSET)

        volume_snapshots = d.pop("volumeSnapshots", UNSET)

        backup_job_advanced_settings_hyper_v_model = cls(
            guest_quiescence=guest_quiescence,
            changed_block_tracking=changed_block_tracking,
            volume_snapshots=volume_snapshots,
        )

        backup_job_advanced_settings_hyper_v_model.additional_properties = d
        return backup_job_advanced_settings_hyper_v_model

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
