from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_filter_expression_type import EFilterExpressionType
from ..models.e_group_expression_operation_type import EGroupExpressionOperationType

if TYPE_CHECKING:
    from ..models.filter_expression_model import FilterExpressionModel


T = TypeVar("T", bound="GroupExpressionModel")


@_attrs_define
class GroupExpressionModel:
    """Group expression.

    Attributes:
        type_ (EFilterExpressionType): Expression type.
        operation (EGroupExpressionOperationType): Group operation (logical operator).
        items (list[FilterExpressionModel]): Array of predicate and group expressions.
    """

    type_: EFilterExpressionType
    operation: EGroupExpressionOperationType
    items: list[FilterExpressionModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        operation = self.operation.value

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "operation": operation,
                "items": items,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.filter_expression_model import FilterExpressionModel

        d = dict(src_dict)
        type_ = EFilterExpressionType(d.pop("type"))

        operation = EGroupExpressionOperationType(d.pop("operation"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = FilterExpressionModel.from_dict(items_item_data)

            items.append(items_item)

        group_expression_model = cls(
            type_=type_,
            operation=operation,
            items=items,
        )

        group_expression_model.additional_properties = d
        return group_expression_model

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
