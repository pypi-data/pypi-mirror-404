from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_windows_host_component_type import EWindowsHostComponentType

T = TypeVar("T", bound="WindowsHostComponentPortModel")


@_attrs_define
class WindowsHostComponentPortModel:
    """Ports used by Veeam Backup & Replication components.

    Attributes:
        component_name (EWindowsHostComponentType): Veeam Backup & Replication component.
        port (int): Port used by the component.
    """

    component_name: EWindowsHostComponentType
    port: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        component_name = self.component_name.value

        port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "componentName": component_name,
                "port": port,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        component_name = EWindowsHostComponentType(d.pop("componentName"))

        port = d.pop("port")

        windows_host_component_port_model = cls(
            component_name=component_name,
            port=port,
        )

        windows_host_component_port_model.additional_properties = d
        return windows_host_component_port_model

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
