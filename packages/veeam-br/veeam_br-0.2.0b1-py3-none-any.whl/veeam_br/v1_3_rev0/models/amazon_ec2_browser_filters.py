from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AmazonEC2BrowserFilters")


@_attrs_define
class AmazonEC2BrowserFilters:
    """Amazon EC2 hierarchy filters. Using the filters reduces not only the number of records in the response body but also
    the response time.

        Attributes:
            region_id (str): Filters Amazon EC2 resources by AWS region.
    """

    region_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        region_id = self.region_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "regionId": region_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        region_id = d.pop("regionId")

        amazon_ec2_browser_filters = cls(
            region_id=region_id,
        )

        amazon_ec2_browser_filters.additional_properties = d
        return amazon_ec2_browser_filters

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
