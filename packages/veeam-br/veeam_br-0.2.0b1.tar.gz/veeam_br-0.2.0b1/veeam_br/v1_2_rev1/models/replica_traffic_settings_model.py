from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_compression_level import ECompressionLevel
from ..models.e_storage_optimization import EStorageOptimization
from ..types import UNSET, Unset

T = TypeVar("T", bound="ReplicaTrafficSettingsModel")


@_attrs_define
class ReplicaTrafficSettingsModel:
    """Traffic settings.

    Attributes:
        exclude_swap_file_blocks (bool | Unset): If `true`, Veeam Backup & Replication excludes swap file blocks from
            processing.
        exclude_deleted_file_blocks (bool | Unset): If `true`, Veeam Backup & Replication does not copy deleted file
            blocks.
        compression_level (ECompressionLevel | Unset): Compression level.
        storage_optimization (EStorageOptimization | Unset): Storage optimization (depends on the target storage type
            and the size of your files).
    """

    exclude_swap_file_blocks: bool | Unset = UNSET
    exclude_deleted_file_blocks: bool | Unset = UNSET
    compression_level: ECompressionLevel | Unset = UNSET
    storage_optimization: EStorageOptimization | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exclude_swap_file_blocks = self.exclude_swap_file_blocks

        exclude_deleted_file_blocks = self.exclude_deleted_file_blocks

        compression_level: str | Unset = UNSET
        if not isinstance(self.compression_level, Unset):
            compression_level = self.compression_level.value

        storage_optimization: str | Unset = UNSET
        if not isinstance(self.storage_optimization, Unset):
            storage_optimization = self.storage_optimization.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exclude_swap_file_blocks is not UNSET:
            field_dict["excludeSwapFileBlocks"] = exclude_swap_file_blocks
        if exclude_deleted_file_blocks is not UNSET:
            field_dict["excludeDeletedFileBlocks"] = exclude_deleted_file_blocks
        if compression_level is not UNSET:
            field_dict["compressionLevel"] = compression_level
        if storage_optimization is not UNSET:
            field_dict["storageOptimization"] = storage_optimization

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        exclude_swap_file_blocks = d.pop("excludeSwapFileBlocks", UNSET)

        exclude_deleted_file_blocks = d.pop("excludeDeletedFileBlocks", UNSET)

        _compression_level = d.pop("compressionLevel", UNSET)
        compression_level: ECompressionLevel | Unset
        if isinstance(_compression_level, Unset):
            compression_level = UNSET
        else:
            compression_level = ECompressionLevel(_compression_level)

        _storage_optimization = d.pop("storageOptimization", UNSET)
        storage_optimization: EStorageOptimization | Unset
        if isinstance(_storage_optimization, Unset):
            storage_optimization = UNSET
        else:
            storage_optimization = EStorageOptimization(_storage_optimization)

        replica_traffic_settings_model = cls(
            exclude_swap_file_blocks=exclude_swap_file_blocks,
            exclude_deleted_file_blocks=exclude_deleted_file_blocks,
            compression_level=compression_level,
            storage_optimization=storage_optimization,
        )

        replica_traffic_settings_model.additional_properties = d
        return replica_traffic_settings_model

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
