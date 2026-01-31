from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.repository_advanced_settings_model import RepositoryAdvancedSettingsModel


T = TypeVar("T", bound="NetworkRepositorySettingsModel")


@_attrs_define
class NetworkRepositorySettingsModel:
    """Repository settings.

    Attributes:
        task_limit_enabled (bool | Unset): If `true`, the maximum number of concurrent tasks is limited.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
        read_write_limit_enabled (bool | Unset): If `true`, reading and writing speed is limited.
        read_write_rate (int | Unset): Maximum rate that restricts the total speed of reading and writing data to the
            backup repository disk.
        advanced_settings (RepositoryAdvancedSettingsModel | Unset): Advanced settings for the backup repository.
    """

    task_limit_enabled: bool | Unset = UNSET
    max_task_count: int | Unset = UNSET
    read_write_limit_enabled: bool | Unset = UNSET
    read_write_rate: int | Unset = UNSET
    advanced_settings: RepositoryAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        task_limit_enabled = self.task_limit_enabled

        max_task_count = self.max_task_count

        read_write_limit_enabled = self.read_write_limit_enabled

        read_write_rate = self.read_write_rate

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if task_limit_enabled is not UNSET:
            field_dict["taskLimitEnabled"] = task_limit_enabled
        if max_task_count is not UNSET:
            field_dict["maxTaskCount"] = max_task_count
        if read_write_limit_enabled is not UNSET:
            field_dict["readWriteLimitEnabled"] = read_write_limit_enabled
        if read_write_rate is not UNSET:
            field_dict["readWriteRate"] = read_write_rate
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.repository_advanced_settings_model import RepositoryAdvancedSettingsModel

        d = dict(src_dict)
        task_limit_enabled = d.pop("taskLimitEnabled", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        read_write_limit_enabled = d.pop("readWriteLimitEnabled", UNSET)

        read_write_rate = d.pop("readWriteRate", UNSET)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: RepositoryAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = RepositoryAdvancedSettingsModel.from_dict(_advanced_settings)

        network_repository_settings_model = cls(
            task_limit_enabled=task_limit_enabled,
            max_task_count=max_task_count,
            read_write_limit_enabled=read_write_limit_enabled,
            read_write_rate=read_write_rate,
            advanced_settings=advanced_settings,
        )

        network_repository_settings_model.additional_properties = d
        return network_repository_settings_model

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
