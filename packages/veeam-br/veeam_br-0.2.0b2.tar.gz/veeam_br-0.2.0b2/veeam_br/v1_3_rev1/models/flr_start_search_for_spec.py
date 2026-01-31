from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrStartSearchForSpec")


@_attrs_define
class FlrStartSearchForSpec:
    """Search files and folders.

    Attributes:
        path (str): Search path.
        search_string (str): Search string. The following wildcard characters are supported&#58; "*", "?" and "+".
        disable_recursive_search (bool | Unset): If `true`, Veeam Backup & Replication will not search the child
            folders, only the files in the parent folder.
    """

    path: str
    search_string: str
    disable_recursive_search: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        search_string = self.search_string

        disable_recursive_search = self.disable_recursive_search

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "searchString": search_string,
            }
        )
        if disable_recursive_search is not UNSET:
            field_dict["disableRecursiveSearch"] = disable_recursive_search

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        search_string = d.pop("searchString")

        disable_recursive_search = d.pop("disableRecursiveSearch", UNSET)

        flr_start_search_for_spec = cls(
            path=path,
            search_string=search_string,
            disable_recursive_search=disable_recursive_search,
        )

        flr_start_search_for_spec.additional_properties = d
        return flr_start_search_for_spec

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
