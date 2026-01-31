from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination_result import PaginationResult
    from ..models.unstructured_data_flr_browse_item_model import UnstructuredDataFlrBrowseItemModel


T = TypeVar("T", bound="UnstructuredDataFlrBrowseFolderModel")


@_attrs_define
class UnstructuredDataFlrBrowseFolderModel:
    """Item content.

    Attributes:
        path (str): Browsing path.
        items (list[UnstructuredDataFlrBrowseItemModel]): Array of child items.
        pagination (PaginationResult | Unset): Pagination settings.
    """

    path: str
    items: list[UnstructuredDataFlrBrowseItemModel]
    pagination: PaginationResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "items": items,
            }
        )
        if pagination is not UNSET:
            field_dict["pagination"] = pagination

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination_result import PaginationResult
        from ..models.unstructured_data_flr_browse_item_model import UnstructuredDataFlrBrowseItemModel

        d = dict(src_dict)
        path = d.pop("path")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = UnstructuredDataFlrBrowseItemModel.from_dict(items_item_data)

            items.append(items_item)

        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationResult | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationResult.from_dict(_pagination)

        unstructured_data_flr_browse_folder_model = cls(
            path=path,
            items=items,
            pagination=pagination,
        )

        unstructured_data_flr_browse_folder_model.additional_properties = d
        return unstructured_data_flr_browse_folder_model

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
