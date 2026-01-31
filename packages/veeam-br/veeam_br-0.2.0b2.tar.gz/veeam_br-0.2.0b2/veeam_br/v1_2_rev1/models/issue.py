from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bottleneck_severity import BottleneckSeverity
from ..models.bottleneck_type import BottleneckType

T = TypeVar("T", bound="Issue")


@_attrs_define
class Issue:
    """Issue status.

    Attributes:
        severity (BottleneckSeverity): Bottleneck severity.
        bottleneck (BottleneckType): Bottleneck type.
    """

    severity: BottleneckSeverity
    bottleneck: BottleneckType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        severity = self.severity.value

        bottleneck = self.bottleneck.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "severity": severity,
                "bottleneck": bottleneck,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        severity = BottleneckSeverity(d.pop("severity"))

        bottleneck = BottleneckType(d.pop("bottleneck"))

        issue = cls(
            severity=severity,
            bottleneck=bottleneck,
        )

        issue.additional_properties = d
        return issue

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
