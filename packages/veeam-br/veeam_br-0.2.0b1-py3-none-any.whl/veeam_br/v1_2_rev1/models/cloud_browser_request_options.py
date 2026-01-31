from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudBrowserRequestOptions")


@_attrs_define
class CloudBrowserRequestOptions:
    """
    Attributes:
        reset_cache (bool | Unset): If `true`, the cache will be reset for this request. Resetting the cache slows down
            request processing but it allows you to get up-to-date data.
    """

    reset_cache: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reset_cache = self.reset_cache

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if reset_cache is not UNSET:
            field_dict["resetCache"] = reset_cache

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reset_cache = d.pop("resetCache", UNSET)

        cloud_browser_request_options = cls(
            reset_cache=reset_cache,
        )

        cloud_browser_request_options.additional_properties = d
        return cloud_browser_request_options

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
