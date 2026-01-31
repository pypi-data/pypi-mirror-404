from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.v_sphere_changed_block_tracking_settings_model import VSphereChangedBlockTrackingSettingsModel


T = TypeVar("T", bound="BackupJobAdvancedSettingsVSphereModel")


@_attrs_define
class BackupJobAdvancedSettingsVSphereModel:
    """VMware vSphere settings for the job.

    Attributes:
        enable_vm_ware_tools_quiescence (bool | Unset): If `true`, VMware Tools quiescence is enabled for freezing the
            VM file system and application data.
        changed_block_tracking (VSphereChangedBlockTrackingSettingsModel | Unset): Changed block tracking (CBT) settings
            for the job.
    """

    enable_vm_ware_tools_quiescence: bool | Unset = UNSET
    changed_block_tracking: VSphereChangedBlockTrackingSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enable_vm_ware_tools_quiescence = self.enable_vm_ware_tools_quiescence

        changed_block_tracking: dict[str, Any] | Unset = UNSET
        if not isinstance(self.changed_block_tracking, Unset):
            changed_block_tracking = self.changed_block_tracking.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enable_vm_ware_tools_quiescence is not UNSET:
            field_dict["enableVMWareToolsQuiescence"] = enable_vm_ware_tools_quiescence
        if changed_block_tracking is not UNSET:
            field_dict["changedBlockTracking"] = changed_block_tracking

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v_sphere_changed_block_tracking_settings_model import VSphereChangedBlockTrackingSettingsModel

        d = dict(src_dict)
        enable_vm_ware_tools_quiescence = d.pop("enableVMWareToolsQuiescence", UNSET)

        _changed_block_tracking = d.pop("changedBlockTracking", UNSET)
        changed_block_tracking: VSphereChangedBlockTrackingSettingsModel | Unset
        if isinstance(_changed_block_tracking, Unset):
            changed_block_tracking = UNSET
        else:
            changed_block_tracking = VSphereChangedBlockTrackingSettingsModel.from_dict(_changed_block_tracking)

        backup_job_advanced_settings_v_sphere_model = cls(
            enable_vm_ware_tools_quiescence=enable_vm_ware_tools_quiescence,
            changed_block_tracking=changed_block_tracking,
        )

        backup_job_advanced_settings_v_sphere_model.additional_properties = d
        return backup_job_advanced_settings_v_sphere_model

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
