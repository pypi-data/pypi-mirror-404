from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_virus_detection_action import EVirusDetectionAction
from ..types import UNSET, Unset

T = TypeVar("T", bound="SecureRestoreSpec")


@_attrs_define
class SecureRestoreSpec:
    """Secure restore settings.

    Attributes:
        antivirus_scan_enabled (bool): If `true`, Veeam Backup & Replication scans machine data with antivirus software
            before restoring the machine to the production environment.
        virus_detection_action (EVirusDetectionAction | Unset): Action that Veeam Backup & Replication takes if the
            antivirus software finds a threat.
        entire_volume_scan_enabled (bool | Unset): If `true`, the antivirus continues machine scan after the first
            malware is found.
    """

    antivirus_scan_enabled: bool
    virus_detection_action: EVirusDetectionAction | Unset = UNSET
    entire_volume_scan_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        antivirus_scan_enabled = self.antivirus_scan_enabled

        virus_detection_action: str | Unset = UNSET
        if not isinstance(self.virus_detection_action, Unset):
            virus_detection_action = self.virus_detection_action.value

        entire_volume_scan_enabled = self.entire_volume_scan_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "antivirusScanEnabled": antivirus_scan_enabled,
            }
        )
        if virus_detection_action is not UNSET:
            field_dict["virusDetectionAction"] = virus_detection_action
        if entire_volume_scan_enabled is not UNSET:
            field_dict["entireVolumeScanEnabled"] = entire_volume_scan_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        antivirus_scan_enabled = d.pop("antivirusScanEnabled")

        _virus_detection_action = d.pop("virusDetectionAction", UNSET)
        virus_detection_action: EVirusDetectionAction | Unset
        if isinstance(_virus_detection_action, Unset):
            virus_detection_action = UNSET
        else:
            virus_detection_action = EVirusDetectionAction(_virus_detection_action)

        entire_volume_scan_enabled = d.pop("entireVolumeScanEnabled", UNSET)

        secure_restore_spec = cls(
            antivirus_scan_enabled=antivirus_scan_enabled,
            virus_detection_action=virus_detection_action,
            entire_volume_scan_enabled=entire_volume_scan_enabled,
        )

        secure_restore_spec.additional_properties = d
        return secure_restore_spec

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
