from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_filter_expression_type import EFilterExpressionType
from ..models.e_predicate_expression_operation_type import EPredicateExpressionOperationType

T = TypeVar("T", bound="PredicateExpressionModel")


@_attrs_define
class PredicateExpressionModel:
    """Predicate expression.

    Attributes:
        type_ (EFilterExpressionType): Expression type.
        property_ (str): Name of an `InventoryObjectModel` property to which you want to apply the predicate operation.
            Possible values&#58; *platform*, *size*, *hostName*, *name*, *type*, *objectId*, *urn*. Names of
            `AgentObjectModel` properties are supported in the [Get All Protection Groups](Inventory-
            Browser#operation/GetAllInventoryPGs) request.
        operation (EPredicateExpressionOperationType): Predicate operation (relational operator).
        value (str): Value of the specified `InventoryObjectModel` property.
    """

    type_: EFilterExpressionType
    property_: str
    operation: EPredicateExpressionOperationType
    value: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        property_ = self.property_

        operation = self.operation.value

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "property": property_,
                "operation": operation,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EFilterExpressionType(d.pop("type"))

        property_ = d.pop("property")

        operation = EPredicateExpressionOperationType(d.pop("operation"))

        value = d.pop("value")

        predicate_expression_model = cls(
            type_=type_,
            property_=property_,
            operation=operation,
            value=value,
        )

        predicate_expression_model.additional_properties = d
        return predicate_expression_model

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
