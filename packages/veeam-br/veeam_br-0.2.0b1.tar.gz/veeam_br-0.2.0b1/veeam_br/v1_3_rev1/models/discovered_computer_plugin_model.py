from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_application_plugin_status import EApplicationPluginStatus
from ..models.e_application_plugin_type import EApplicationPluginType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DiscoveredComputerPluginModel")


@_attrs_define
class DiscoveredComputerPluginModel:
    """Plug-in settings of the discovered computer.

    Attributes:
        type_ (EApplicationPluginType | Unset): Plug-in type.
        version (str | Unset): Plug-in version.
        status (EApplicationPluginStatus | Unset): Plug-in status.
    """

    type_: EApplicationPluginType | Unset = UNSET
    version: str | Unset = UNSET
    status: EApplicationPluginStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        version = self.version

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if version is not UNSET:
            field_dict["version"] = version
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: EApplicationPluginType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EApplicationPluginType(_type_)

        version = d.pop("version", UNSET)

        _status = d.pop("status", UNSET)
        status: EApplicationPluginStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = EApplicationPluginStatus(_status)

        discovered_computer_plugin_model = cls(
            type_=type_,
            version=version,
            status=status,
        )

        discovered_computer_plugin_model.additional_properties = d
        return discovered_computer_plugin_model

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
