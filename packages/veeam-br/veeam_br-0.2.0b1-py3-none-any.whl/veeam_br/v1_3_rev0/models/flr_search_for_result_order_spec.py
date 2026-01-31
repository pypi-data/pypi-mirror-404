from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_browse_order_type import EFlrBrowseOrderType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrSearchForResultOrderSpec")


@_attrs_define
class FlrSearchForResultOrderSpec:
    """Sorting settings.

    Attributes:
        order_column (EFlrBrowseOrderType): Sorts items by one of the following parameters.
        order_asc (bool | Unset): If `true`, sorts items in the ascending order by the `orderColumn` parameter.
    """

    order_column: EFlrBrowseOrderType
    order_asc: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_column = self.order_column.value

        order_asc = self.order_asc

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orderColumn": order_column,
            }
        )
        if order_asc is not UNSET:
            field_dict["orderAsc"] = order_asc

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        order_column = EFlrBrowseOrderType(d.pop("orderColumn"))

        order_asc = d.pop("orderAsc", UNSET)

        flr_search_for_result_order_spec = cls(
            order_column=order_column,
            order_asc=order_asc,
        )

        flr_search_for_result_order_spec.additional_properties = d
        return flr_search_for_result_order_spec

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
