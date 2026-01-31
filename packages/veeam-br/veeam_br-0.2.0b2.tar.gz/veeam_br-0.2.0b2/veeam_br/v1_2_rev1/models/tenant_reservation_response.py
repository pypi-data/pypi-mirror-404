from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tenant_load_calculator_response import TenantLoadCalculatorResponse


T = TypeVar("T", bound="TenantReservationResponse")


@_attrs_define
class TenantReservationResponse:
    """
    Attributes:
        azure_tenant_id (str): Tenant ID assigned by Microsoft Entra ID.
        expiration (datetime.datetime | Unset): Date and time when the tenant reservation expires.
        calculated_consumption (TenantLoadCalculatorResponse | Unset):
    """

    azure_tenant_id: str
    expiration: datetime.datetime | Unset = UNSET
    calculated_consumption: TenantLoadCalculatorResponse | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_tenant_id = self.azure_tenant_id

        expiration: str | Unset = UNSET
        if not isinstance(self.expiration, Unset):
            expiration = self.expiration.isoformat()

        calculated_consumption: dict[str, Any] | Unset = UNSET
        if not isinstance(self.calculated_consumption, Unset):
            calculated_consumption = self.calculated_consumption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "azureTenantId": azure_tenant_id,
            }
        )
        if expiration is not UNSET:
            field_dict["expiration"] = expiration
        if calculated_consumption is not UNSET:
            field_dict["calculatedConsumption"] = calculated_consumption

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tenant_load_calculator_response import TenantLoadCalculatorResponse

        d = dict(src_dict)
        azure_tenant_id = d.pop("azureTenantId")

        _expiration = d.pop("expiration", UNSET)
        expiration: datetime.datetime | Unset
        if isinstance(_expiration, Unset):
            expiration = UNSET
        else:
            expiration = isoparse(_expiration)

        _calculated_consumption = d.pop("calculatedConsumption", UNSET)
        calculated_consumption: TenantLoadCalculatorResponse | Unset
        if isinstance(_calculated_consumption, Unset):
            calculated_consumption = UNSET
        else:
            calculated_consumption = TenantLoadCalculatorResponse.from_dict(_calculated_consumption)

        tenant_reservation_response = cls(
            azure_tenant_id=azure_tenant_id,
            expiration=expiration,
            calculated_consumption=calculated_consumption,
        )

        tenant_reservation_response.additional_properties = d
        return tenant_reservation_response

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
