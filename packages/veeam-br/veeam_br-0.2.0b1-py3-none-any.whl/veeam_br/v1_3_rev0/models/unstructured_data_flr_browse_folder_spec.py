from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_browse_filtration_model import FlrBrowseFiltrationModel
    from ..models.flr_browse_order_spec import FlrBrowseOrderSpec
    from ..models.pagination_spec import PaginationSpec


T = TypeVar("T", bound="UnstructuredDataFlrBrowseFolderSpec")


@_attrs_define
class UnstructuredDataFlrBrowseFolderSpec:
    """Browser settings.

    Attributes:
        path (str): Browsing path.
        filter_ (FlrBrowseFiltrationModel | Unset): Filter settings.
        order (FlrBrowseOrderSpec | Unset): Sorting settings.
        pagination (PaginationSpec | Unset): Pagination settings.
    """

    path: str
    filter_: FlrBrowseFiltrationModel | Unset = UNSET
    order: FlrBrowseOrderSpec | Unset = UNSET
    pagination: PaginationSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        filter_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = self.filter_.to_dict()

        order: dict[str, Any] | Unset = UNSET
        if not isinstance(self.order, Unset):
            order = self.order.to_dict()

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
            }
        )
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if order is not UNSET:
            field_dict["order"] = order
        if pagination is not UNSET:
            field_dict["pagination"] = pagination

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_browse_filtration_model import FlrBrowseFiltrationModel
        from ..models.flr_browse_order_spec import FlrBrowseOrderSpec
        from ..models.pagination_spec import PaginationSpec

        d = dict(src_dict)
        path = d.pop("path")

        _filter_ = d.pop("filter", UNSET)
        filter_: FlrBrowseFiltrationModel | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = FlrBrowseFiltrationModel.from_dict(_filter_)

        _order = d.pop("order", UNSET)
        order: FlrBrowseOrderSpec | Unset
        if isinstance(_order, Unset):
            order = UNSET
        else:
            order = FlrBrowseOrderSpec.from_dict(_order)

        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationSpec | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationSpec.from_dict(_pagination)

        unstructured_data_flr_browse_folder_spec = cls(
            path=path,
            filter_=filter_,
            order=order,
            pagination=pagination,
        )

        unstructured_data_flr_browse_folder_spec.additional_properties = d
        return unstructured_data_flr_browse_folder_spec

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
