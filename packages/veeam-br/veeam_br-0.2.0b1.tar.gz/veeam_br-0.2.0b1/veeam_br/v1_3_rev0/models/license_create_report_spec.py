from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_license_report_format import ELicenseReportFormat

T = TypeVar("T", bound="LicenseCreateReportSpec")


@_attrs_define
class LicenseCreateReportSpec:
    """Create a report on license usage.

    Attributes:
        report_format (ELicenseReportFormat): Format of the license usage report.
    """

    report_format: ELicenseReportFormat
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        report_format = self.report_format.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reportFormat": report_format,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        report_format = ELicenseReportFormat(d.pop("reportFormat"))

        license_create_report_spec = cls(
            report_format=report_format,
        )

        license_create_report_spec.additional_properties = d
        return license_create_report_spec

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
