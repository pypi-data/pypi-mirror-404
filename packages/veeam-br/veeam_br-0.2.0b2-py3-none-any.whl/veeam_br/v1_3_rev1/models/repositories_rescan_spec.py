from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RepositoriesRescanSpec")


@_attrs_define
class RepositoriesRescanSpec:
    """Settings for backup repository rescan.

    Attributes:
        repository_ids (list[UUID]): Array of repository IDs to rescan.
    """

    repository_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        repository_ids = []
        for repository_ids_item_data in self.repository_ids:
            repository_ids_item = str(repository_ids_item_data)
            repository_ids.append(repository_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "repositoryIds": repository_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        repository_ids = []
        _repository_ids = d.pop("repositoryIds")
        for repository_ids_item_data in _repository_ids:
            repository_ids_item = UUID(repository_ids_item_data)

            repository_ids.append(repository_ids_item)

        repositories_rescan_spec = cls(
            repository_ids=repository_ids,
        )

        repositories_rescan_spec.additional_properties = d
        return repositories_rescan_spec

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
