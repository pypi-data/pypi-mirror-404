from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_speed_unit import ESpeedUnit
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_window_setting_model import BackupWindowSettingModel


T = TypeVar("T", bound="TrafficRuleModel")


@_attrs_define
class TrafficRuleModel:
    """Global network traffic rule.

    Attributes:
        name (str): Name of the rule.
        source_ip_start (str): Start IP address of the range for the backup infrastructure components on the source
            side.
        source_ip_end (str): End IP address of the range for the backup infrastructure components on the source side.
        target_ip_start (str): Start IP address of the range for the backup infrastructure components on the target
            side.
        target_ip_end (str): End IP address of the range for the backup infrastructure components on the target side.
        id (UUID | Unset): ID of the rule.
        encryption_enabled (bool | Unset): If `true`, traffic encryption is enabled.
        throttling_enabled (bool | Unset): If `true`, traffic throttling is enabled.
        throttling_unit (ESpeedUnit | Unset): Traffic speed unit.
        throttling_value (int | Unset): Maximum speed that must be used to transfer data from source to target.
        throttling_window_enabled (bool | Unset): If `true`, throttling window during which the speed must be limited is
            enabled.
        throttling_window_options (BackupWindowSettingModel | Unset): Time scheme that defines permitted days and hours
            for the job to start.
    """

    name: str
    source_ip_start: str
    source_ip_end: str
    target_ip_start: str
    target_ip_end: str
    id: UUID | Unset = UNSET
    encryption_enabled: bool | Unset = UNSET
    throttling_enabled: bool | Unset = UNSET
    throttling_unit: ESpeedUnit | Unset = UNSET
    throttling_value: int | Unset = UNSET
    throttling_window_enabled: bool | Unset = UNSET
    throttling_window_options: BackupWindowSettingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        source_ip_start = self.source_ip_start

        source_ip_end = self.source_ip_end

        target_ip_start = self.target_ip_start

        target_ip_end = self.target_ip_end

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        encryption_enabled = self.encryption_enabled

        throttling_enabled = self.throttling_enabled

        throttling_unit: str | Unset = UNSET
        if not isinstance(self.throttling_unit, Unset):
            throttling_unit = self.throttling_unit.value

        throttling_value = self.throttling_value

        throttling_window_enabled = self.throttling_window_enabled

        throttling_window_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.throttling_window_options, Unset):
            throttling_window_options = self.throttling_window_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "sourceIPStart": source_ip_start,
                "sourceIPEnd": source_ip_end,
                "targetIPStart": target_ip_start,
                "targetIPEnd": target_ip_end,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if encryption_enabled is not UNSET:
            field_dict["encryptionEnabled"] = encryption_enabled
        if throttling_enabled is not UNSET:
            field_dict["throttlingEnabled"] = throttling_enabled
        if throttling_unit is not UNSET:
            field_dict["throttlingUnit"] = throttling_unit
        if throttling_value is not UNSET:
            field_dict["throttlingValue"] = throttling_value
        if throttling_window_enabled is not UNSET:
            field_dict["throttlingWindowEnabled"] = throttling_window_enabled
        if throttling_window_options is not UNSET:
            field_dict["throttlingWindowOptions"] = throttling_window_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_window_setting_model import BackupWindowSettingModel

        d = dict(src_dict)
        name = d.pop("name")

        source_ip_start = d.pop("sourceIPStart")

        source_ip_end = d.pop("sourceIPEnd")

        target_ip_start = d.pop("targetIPStart")

        target_ip_end = d.pop("targetIPEnd")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        encryption_enabled = d.pop("encryptionEnabled", UNSET)

        throttling_enabled = d.pop("throttlingEnabled", UNSET)

        _throttling_unit = d.pop("throttlingUnit", UNSET)
        throttling_unit: ESpeedUnit | Unset
        if isinstance(_throttling_unit, Unset):
            throttling_unit = UNSET
        else:
            throttling_unit = ESpeedUnit(_throttling_unit)

        throttling_value = d.pop("throttlingValue", UNSET)

        throttling_window_enabled = d.pop("throttlingWindowEnabled", UNSET)

        _throttling_window_options = d.pop("throttlingWindowOptions", UNSET)
        throttling_window_options: BackupWindowSettingModel | Unset
        if isinstance(_throttling_window_options, Unset):
            throttling_window_options = UNSET
        else:
            throttling_window_options = BackupWindowSettingModel.from_dict(_throttling_window_options)

        traffic_rule_model = cls(
            name=name,
            source_ip_start=source_ip_start,
            source_ip_end=source_ip_end,
            target_ip_start=target_ip_start,
            target_ip_end=target_ip_end,
            id=id,
            encryption_enabled=encryption_enabled,
            throttling_enabled=throttling_enabled,
            throttling_unit=throttling_unit,
            throttling_value=throttling_value,
            throttling_window_enabled=throttling_window_enabled,
            throttling_window_options=throttling_window_options,
        )

        traffic_rule_model.additional_properties = d
        return traffic_rule_model

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
