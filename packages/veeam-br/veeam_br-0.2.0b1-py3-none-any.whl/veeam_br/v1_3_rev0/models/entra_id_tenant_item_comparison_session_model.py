from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.entra_id_tenant_item_comparison_session_model_status import EntraIdTenantItemComparisonSessionModelStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_item_comparison_model import EntraIdTenantItemComparisonModel


T = TypeVar("T", bound="EntraIdTenantItemComparisonSessionModel")


@_attrs_define
class EntraIdTenantItemComparisonSessionModel:
    """Comparison session.

    Attributes:
        status (EntraIdTenantItemComparisonSessionModelStatus): Session status.
        result (EntraIdTenantItemComparisonModel | Unset): Comparison result.
        error_message (str | Unset): Error message.
    """

    status: EntraIdTenantItemComparisonSessionModelStatus
    result: EntraIdTenantItemComparisonModel | Unset = UNSET
    error_message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if result is not UNSET:
            field_dict["result"] = result
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_item_comparison_model import EntraIdTenantItemComparisonModel

        d = dict(src_dict)
        status = EntraIdTenantItemComparisonSessionModelStatus(d.pop("status"))

        _result = d.pop("result", UNSET)
        result: EntraIdTenantItemComparisonModel | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = EntraIdTenantItemComparisonModel.from_dict(_result)

        error_message = d.pop("errorMessage", UNSET)

        entra_id_tenant_item_comparison_session_model = cls(
            status=status,
            result=result,
            error_message=error_message,
        )

        entra_id_tenant_item_comparison_session_model.additional_properties = d
        return entra_id_tenant_item_comparison_session_model

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
