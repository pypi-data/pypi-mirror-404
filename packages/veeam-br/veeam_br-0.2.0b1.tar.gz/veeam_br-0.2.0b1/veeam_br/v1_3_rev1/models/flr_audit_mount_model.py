from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.flr_task_item_model import FlrTaskItemModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="FlrAuditMountModel")


@_attrs_define
class FlrAuditMountModel:
    """Items restored during one file restore session.

    Attributes:
        items (list[FlrTaskItemModel]): Array of items restored during one file restore session.
        pagination (PaginationResult): Pagination settings.
    """

    items: list[FlrTaskItemModel]
    pagination: PaginationResult
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_task_item_model import FlrTaskItemModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = FlrTaskItemModel.from_dict(items_item_data)

            items.append(items_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        flr_audit_mount_model = cls(
            items=items,
            pagination=pagination,
        )

        flr_audit_mount_model.additional_properties = d
        return flr_audit_mount_model

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
