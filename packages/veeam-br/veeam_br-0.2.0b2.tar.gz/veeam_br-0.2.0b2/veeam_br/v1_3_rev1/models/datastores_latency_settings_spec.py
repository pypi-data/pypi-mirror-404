from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="DatastoresLatencySettingsSpec")


@_attrs_define
class DatastoresLatencySettingsSpec:
    """Datastore latency settings.

    Attributes:
        storage_object (InventoryObjectModel): Inventory object properties.
        latency_limit_ms (int | Unset): I/O latency threshold (in milliseconds) at which Veeam Backup & Replication will
            stop assigning new tasks to the datastore or volume. Default: 20.
        throttling_io_limit_ms (int | Unset): I/O latency limit (in milliseconds) at which Veeam Backup & Replication
            will slow down read and write operations for the datastore or volume.<p>`latencyLimitMs` must not be greater
            than `throttlingIOLimitMs`.</p> Default: 30.
    """

    storage_object: InventoryObjectModel
    latency_limit_ms: int | Unset = 20
    throttling_io_limit_ms: int | Unset = 30
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage_object = self.storage_object.to_dict()

        latency_limit_ms = self.latency_limit_ms

        throttling_io_limit_ms = self.throttling_io_limit_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "storageObject": storage_object,
            }
        )
        if latency_limit_ms is not UNSET:
            field_dict["latencyLimitMs"] = latency_limit_ms
        if throttling_io_limit_ms is not UNSET:
            field_dict["throttlingIOLimitMs"] = throttling_io_limit_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        storage_object = InventoryObjectModel.from_dict(d.pop("storageObject"))

        latency_limit_ms = d.pop("latencyLimitMs", UNSET)

        throttling_io_limit_ms = d.pop("throttlingIOLimitMs", UNSET)

        datastores_latency_settings_spec = cls(
            storage_object=storage_object,
            latency_limit_ms=latency_limit_ms,
            throttling_io_limit_ms=throttling_io_limit_ms,
        )

        datastores_latency_settings_spec.additional_properties = d
        return datastores_latency_settings_spec

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
