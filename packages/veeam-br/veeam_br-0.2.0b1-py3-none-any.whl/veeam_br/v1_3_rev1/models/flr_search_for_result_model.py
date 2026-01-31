from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_browser_item_model import FlrBrowserItemModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="FlrSearchForResultModel")


@_attrs_define
class FlrSearchForResultModel:
    """Search results.

    Attributes:
        search_string (str): Search string.
        items (list[FlrBrowserItemModel]): Array of child items.
        path (str | Unset): Search path.
        pagination (PaginationResult | Unset): Pagination settings.
    """

    search_string: str
    items: list[FlrBrowserItemModel]
    path: str | Unset = UNSET
    pagination: PaginationResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        search_string = self.search_string

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        path = self.path

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "searchString": search_string,
                "items": items,
            }
        )
        if path is not UNSET:
            field_dict["path"] = path
        if pagination is not UNSET:
            field_dict["pagination"] = pagination

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_browser_item_model import FlrBrowserItemModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        search_string = d.pop("searchString")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = FlrBrowserItemModel.from_dict(items_item_data)

            items.append(items_item)

        path = d.pop("path", UNSET)

        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationResult | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationResult.from_dict(_pagination)

        flr_search_for_result_model = cls(
            search_string=search_string,
            items=items,
            path=path,
            pagination=pagination,
        )

        flr_search_for_result_model.additional_properties = d
        return flr_search_for_result_model

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
