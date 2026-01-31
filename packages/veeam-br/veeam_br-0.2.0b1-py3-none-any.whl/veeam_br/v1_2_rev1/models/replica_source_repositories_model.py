from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.evm_data_source_repository_type import EVMDataSourceRepositoryType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ReplicaSourceRepositoriesModel")


@_attrs_define
class ReplicaSourceRepositoriesModel:
    """Source to obtain VM data from.

    Attributes:
        source_type (EVMDataSourceRepositoryType): Data source type.
        repository_ids (list[UUID] | Unset): Array of repository IDs to obtain data from.
    """

    source_type: EVMDataSourceRepositoryType
    repository_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        repository_ids: list[str] | Unset = UNSET
        if not isinstance(self.repository_ids, Unset):
            repository_ids = []
            for repository_ids_item_data in self.repository_ids:
                repository_ids_item = str(repository_ids_item_data)
                repository_ids.append(repository_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourceType": source_type,
            }
        )
        if repository_ids is not UNSET:
            field_dict["repositoryIds"] = repository_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_type = EVMDataSourceRepositoryType(d.pop("sourceType"))

        _repository_ids = d.pop("repositoryIds", UNSET)
        repository_ids: list[UUID] | Unset = UNSET
        if _repository_ids is not UNSET:
            repository_ids = []
            for repository_ids_item_data in _repository_ids:
                repository_ids_item = UUID(repository_ids_item_data)

                repository_ids.append(repository_ids_item)

        replica_source_repositories_model = cls(
            source_type=source_type,
            repository_ids=repository_ids,
        )

        replica_source_repositories_model.additional_properties = d
        return replica_source_repositories_model

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
