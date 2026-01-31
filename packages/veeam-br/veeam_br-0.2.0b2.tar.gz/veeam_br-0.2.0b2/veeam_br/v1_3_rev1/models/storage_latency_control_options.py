from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.datastores_latency_settings_model import DatastoresLatencySettingsModel


T = TypeVar("T", bound="StorageLatencyControlOptions")


@_attrs_define
class StorageLatencyControlOptions:
    """Latency control options.

    Attributes:
        latency_limit_ms (int): I/O latency threshold (in milliseconds) at which Veeam Backup & Replication will stop
            assigning new tasks to datastores or volumes. Default: 20.
        throttling_io_limit_ms (int): I/O latency limit (in milliseconds) at which Veeam Backup & Replication will slow
            down read and write operations for datastores or volumes.<p>`latencyLimitMs` must not be greater than
            `throttlingIOLimitMs`.</p> Default: 30.
        advanced_options (list[DatastoresLatencySettingsModel] | Unset): Array of custom latency thresholds for specific
            datastores.
    """

    latency_limit_ms: int = 20
    throttling_io_limit_ms: int = 30
    advanced_options: list[DatastoresLatencySettingsModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        latency_limit_ms = self.latency_limit_ms

        throttling_io_limit_ms = self.throttling_io_limit_ms

        advanced_options: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.advanced_options, Unset):
            advanced_options = []
            for advanced_options_item_data in self.advanced_options:
                advanced_options_item = advanced_options_item_data.to_dict()
                advanced_options.append(advanced_options_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "latencyLimitMs": latency_limit_ms,
                "throttlingIOLimitMs": throttling_io_limit_ms,
            }
        )
        if advanced_options is not UNSET:
            field_dict["advancedOptions"] = advanced_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.datastores_latency_settings_model import DatastoresLatencySettingsModel

        d = dict(src_dict)
        latency_limit_ms = d.pop("latencyLimitMs")

        throttling_io_limit_ms = d.pop("throttlingIOLimitMs")

        _advanced_options = d.pop("advancedOptions", UNSET)
        advanced_options: list[DatastoresLatencySettingsModel] | Unset = UNSET
        if _advanced_options is not UNSET:
            advanced_options = []
            for advanced_options_item_data in _advanced_options:
                advanced_options_item = DatastoresLatencySettingsModel.from_dict(advanced_options_item_data)

                advanced_options.append(advanced_options_item)

        storage_latency_control_options = cls(
            latency_limit_ms=latency_limit_ms,
            throttling_io_limit_ms=throttling_io_limit_ms,
            advanced_options=advanced_options,
        )

        storage_latency_control_options.additional_properties = d
        return storage_latency_control_options

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
