from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_search_for_result_order_spec import FlrSearchForResultOrderSpec
    from ..models.pagination_spec import PaginationSpec


T = TypeVar("T", bound="FlrSearchForResultSpec")


@_attrs_define
class FlrSearchForResultSpec:
    """Settings for browsing search results.

    Attributes:
        pagination (PaginationSpec | Unset): Pagination settings.
        order (FlrSearchForResultOrderSpec | Unset): Sorting settings.
    """

    pagination: PaginationSpec | Unset = UNSET
    order: FlrSearchForResultOrderSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        order: dict[str, Any] | Unset = UNSET
        if not isinstance(self.order, Unset):
            order = self.order.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if order is not UNSET:
            field_dict["order"] = order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_search_for_result_order_spec import FlrSearchForResultOrderSpec
        from ..models.pagination_spec import PaginationSpec

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationSpec | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationSpec.from_dict(_pagination)

        _order = d.pop("order", UNSET)
        order: FlrSearchForResultOrderSpec | Unset
        if isinstance(_order, Unset):
            order = UNSET
        else:
            order = FlrSearchForResultOrderSpec.from_dict(_order)

        flr_search_for_result_spec = cls(
            pagination=pagination,
            order=order,
        )

        flr_search_for_result_spec.additional_properties = d
        return flr_search_for_result_spec

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
