from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WANAcceleratorPopulateCacheSpec")


@_attrs_define
class WANAcceleratorPopulateCacheSpec:
    """
    Attributes:
        repository_ids (list[UUID] | Unset):
    """

    repository_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        repository_ids: list[str] | Unset = UNSET
        if not isinstance(self.repository_ids, Unset):
            repository_ids = []
            for repository_ids_item_data in self.repository_ids:
                repository_ids_item = str(repository_ids_item_data)
                repository_ids.append(repository_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if repository_ids is not UNSET:
            field_dict["repositoryIds"] = repository_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _repository_ids = d.pop("repositoryIds", UNSET)
        repository_ids: list[UUID] | Unset = UNSET
        if _repository_ids is not UNSET:
            repository_ids = []
            for repository_ids_item_data in _repository_ids:
                repository_ids_item = UUID(repository_ids_item_data)

                repository_ids.append(repository_ids_item)

        wan_accelerator_populate_cache_spec = cls(
            repository_ids=repository_ids,
        )

        wan_accelerator_populate_cache_spec.additional_properties = d
        return wan_accelerator_populate_cache_spec

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
