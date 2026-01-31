from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDeploymentKitSpec")


@_attrs_define
class CreateDeploymentKitSpec:
    """Deployment kit settings.

    Attributes:
        validity_period_hours (int | Unset): Number of hours before the certificate in the deployment kit expires. If
            you do not provide a request body, the default value is 24 hours.
    """

    validity_period_hours: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        validity_period_hours = self.validity_period_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if validity_period_hours is not UNSET:
            field_dict["validityPeriodHours"] = validity_period_hours

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        validity_period_hours = d.pop("validityPeriodHours", UNSET)

        create_deployment_kit_spec = cls(
            validity_period_hours=validity_period_hours,
        )

        create_deployment_kit_spec.additional_properties = d
        return create_deployment_kit_spec

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
