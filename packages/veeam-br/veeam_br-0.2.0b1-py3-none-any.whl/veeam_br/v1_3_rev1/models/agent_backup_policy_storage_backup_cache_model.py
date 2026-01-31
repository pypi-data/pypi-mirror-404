from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_cache_selection_type import EBackupCacheSelectionType
from ..models.e_backup_cache_size_unit import EBackupCacheSizeUnit
from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupPolicyStorageBackupCacheModel")


@_attrs_define
class AgentBackupPolicyStorageBackupCacheModel:
    """Backup cache settings.

    Attributes:
        is_enabled (bool): If `true`, backup cache is enabled. This feature allows you to create restore points in
            temporary local storage where Veeam Agent creates backup files in case a remote backup location is unavailable
            at the time of backup. Note that this option is only supported with Veeam Agent for Microsoft Windows.
        type_ (EBackupCacheSelectionType | Unset): Type of selecting backup cache location.
        local_path (str | Unset): Path to the folder on a protected computer in which backup files will be stored.
            Specify this property if you have specified the `Manual` option for the `type` property.
        size_limit (int | Unset): Maximum size of the backup cache. The unit is specified in the `sizeUnit` property.
        size_unit (EBackupCacheSizeUnit | Unset): Unit for backup cache size.
    """

    is_enabled: bool
    type_: EBackupCacheSelectionType | Unset = UNSET
    local_path: str | Unset = UNSET
    size_limit: int | Unset = UNSET
    size_unit: EBackupCacheSizeUnit | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        local_path = self.local_path

        size_limit = self.size_limit

        size_unit: str | Unset = UNSET
        if not isinstance(self.size_unit, Unset):
            size_unit = self.size_unit.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if local_path is not UNSET:
            field_dict["localPath"] = local_path
        if size_limit is not UNSET:
            field_dict["sizeLimit"] = size_limit
        if size_unit is not UNSET:
            field_dict["sizeUnit"] = size_unit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _type_ = d.pop("type", UNSET)
        type_: EBackupCacheSelectionType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EBackupCacheSelectionType(_type_)

        local_path = d.pop("localPath", UNSET)

        size_limit = d.pop("sizeLimit", UNSET)

        _size_unit = d.pop("sizeUnit", UNSET)
        size_unit: EBackupCacheSizeUnit | Unset
        if isinstance(_size_unit, Unset):
            size_unit = UNSET
        else:
            size_unit = EBackupCacheSizeUnit(_size_unit)

        agent_backup_policy_storage_backup_cache_model = cls(
            is_enabled=is_enabled,
            type_=type_,
            local_path=local_path,
            size_limit=size_limit,
            size_unit=size_unit,
        )

        agent_backup_policy_storage_backup_cache_model.additional_properties = d
        return agent_backup_policy_storage_backup_cache_model

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
