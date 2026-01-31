from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.storage_latency_control_options import StorageLatencyControlOptions


T = TypeVar("T", bound="StorageLatencyControlModel")


@_attrs_define
class StorageLatencyControlModel:
    """Storage latency settings.

    Attributes:
        storage_latency_control_enabled (bool): If `true`, storage latency control is enabled. In this case, you must
            specify the `storageLatencyControlOptions` property. Default: False.
        storage_latency_control_options (StorageLatencyControlOptions | Unset): Latency control options.
    """

    storage_latency_control_enabled: bool = False
    storage_latency_control_options: StorageLatencyControlOptions | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage_latency_control_enabled = self.storage_latency_control_enabled

        storage_latency_control_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage_latency_control_options, Unset):
            storage_latency_control_options = self.storage_latency_control_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "storageLatencyControlEnabled": storage_latency_control_enabled,
            }
        )
        if storage_latency_control_options is not UNSET:
            field_dict["storageLatencyControlOptions"] = storage_latency_control_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.storage_latency_control_options import StorageLatencyControlOptions

        d = dict(src_dict)
        storage_latency_control_enabled = d.pop("storageLatencyControlEnabled")

        _storage_latency_control_options = d.pop("storageLatencyControlOptions", UNSET)
        storage_latency_control_options: StorageLatencyControlOptions | Unset
        if isinstance(_storage_latency_control_options, Unset):
            storage_latency_control_options = UNSET
        else:
            storage_latency_control_options = StorageLatencyControlOptions.from_dict(_storage_latency_control_options)

        storage_latency_control_model = cls(
            storage_latency_control_enabled=storage_latency_control_enabled,
            storage_latency_control_options=storage_latency_control_options,
        )

        storage_latency_control_model.additional_properties = d
        return storage_latency_control_model

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
