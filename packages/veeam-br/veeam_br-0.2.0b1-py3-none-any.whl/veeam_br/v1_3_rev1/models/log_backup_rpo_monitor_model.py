from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_periodically_kinds_backup_copy import EPeriodicallyKindsBackupCopy
from ..types import UNSET, Unset

T = TypeVar("T", bound="LogBackupRPOMonitorModel")


@_attrs_define
class LogBackupRPOMonitorModel:
    """RPO monitor settings if new log backup is not copied.

    Attributes:
        is_enabled (bool): If `true`, there will be a warning if a new transaction log is not copied within the desired
            recovery point objective (RPO).
        type_ (EPeriodicallyKindsBackupCopy | Unset): Time unit for periodic job scheduling.
        quantity (int | Unset): Number of days, hours or minutes within which you will be warned if a log backup is not
            copied.
    """

    is_enabled: bool
    type_: EPeriodicallyKindsBackupCopy | Unset = UNSET
    quantity: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _type_ = d.pop("type", UNSET)
        type_: EPeriodicallyKindsBackupCopy | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EPeriodicallyKindsBackupCopy(_type_)

        quantity = d.pop("quantity", UNSET)

        log_backup_rpo_monitor_model = cls(
            is_enabled=is_enabled,
            type_=type_,
            quantity=quantity,
        )

        log_backup_rpo_monitor_model.additional_properties = d
        return log_backup_rpo_monitor_model

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
