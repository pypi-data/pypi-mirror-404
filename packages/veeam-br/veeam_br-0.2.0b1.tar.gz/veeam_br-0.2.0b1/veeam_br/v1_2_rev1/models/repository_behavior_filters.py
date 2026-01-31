from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryBehaviorFilters")


@_attrs_define
class RepositoryBehaviorFilters:
    """
    Attributes:
        overwrite_owner (bool | Unset):
    """

    overwrite_owner: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        overwrite_owner = self.overwrite_owner

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if overwrite_owner is not UNSET:
            field_dict["overwriteOwner"] = overwrite_owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        overwrite_owner = d.pop("overwriteOwner", UNSET)

        repository_behavior_filters = cls(
            overwrite_owner=overwrite_owner,
        )

        repository_behavior_filters.additional_properties = d
        return repository_behavior_filters

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
