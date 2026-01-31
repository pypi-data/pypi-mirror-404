from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LoadCalculatorRequest")


@_attrs_define
class LoadCalculatorRequest:
    """
    Attributes:
        azure_tenant_id (str): Tenant ID assigned by Microsoft Entra ID.
        application_id (str | Unset): Application ID.
    """

    azure_tenant_id: str
    application_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_tenant_id = self.azure_tenant_id

        application_id = self.application_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "azureTenantId": azure_tenant_id,
            }
        )
        if application_id is not UNSET:
            field_dict["applicationId"] = application_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        azure_tenant_id = d.pop("azureTenantId")

        application_id = d.pop("applicationId", UNSET)

        load_calculator_request = cls(
            azure_tenant_id=azure_tenant_id,
            application_id=application_id,
        )

        load_calculator_request.additional_properties = d
        return load_calculator_request

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
