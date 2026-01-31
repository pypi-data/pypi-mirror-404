from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.windows_host_component_port_model import WindowsHostComponentPortModel


T = TypeVar("T", bound="WindowsHostPortsModel")


@_attrs_define
class WindowsHostPortsModel:
    """Veeam Backup & Replication components installed on the server and ports used by the components.

    Attributes:
        components (list[WindowsHostComponentPortModel] | Unset): Array of Veeam Backup & Replication components.
        port_range_start (int | Unset): Start port used for data transfer.
        port_range_end (int | Unset): End port used for data transfer.
        server_side (bool | Unset): If `true`, the server is run on this side.
    """

    components: list[WindowsHostComponentPortModel] | Unset = UNSET
    port_range_start: int | Unset = UNSET
    port_range_end: int | Unset = UNSET
    server_side: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        components: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.components, Unset):
            components = []
            for components_item_data in self.components:
                components_item = components_item_data.to_dict()
                components.append(components_item)

        port_range_start = self.port_range_start

        port_range_end = self.port_range_end

        server_side = self.server_side

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if components is not UNSET:
            field_dict["components"] = components
        if port_range_start is not UNSET:
            field_dict["portRangeStart"] = port_range_start
        if port_range_end is not UNSET:
            field_dict["portRangeEnd"] = port_range_end
        if server_side is not UNSET:
            field_dict["serverSide"] = server_side

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.windows_host_component_port_model import WindowsHostComponentPortModel

        d = dict(src_dict)
        _components = d.pop("components", UNSET)
        components: list[WindowsHostComponentPortModel] | Unset = UNSET
        if _components is not UNSET:
            components = []
            for components_item_data in _components:
                components_item = WindowsHostComponentPortModel.from_dict(components_item_data)

                components.append(components_item)

        port_range_start = d.pop("portRangeStart", UNSET)

        port_range_end = d.pop("portRangeEnd", UNSET)

        server_side = d.pop("serverSide", UNSET)

        windows_host_ports_model = cls(
            components=components,
            port_range_start=port_range_start,
            port_range_end=port_range_end,
            server_side=server_side,
        )

        windows_host_ports_model.additional_properties = d
        return windows_host_ports_model

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
