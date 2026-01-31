from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_platform_type import EFlrPlatformType

T = TypeVar("T", bound="HyperVLinuxFlrHelperApplianceResourceModel")


@_attrs_define
class HyperVLinuxFlrHelperApplianceResourceModel:
    """Microsoft Hyper-V settings.

    Attributes:
        type_ (EFlrPlatformType): Platform type.
        host (str): Microsoft Hyper-V host where the helper appliance must be registered.
        network (str): Network to which the helper appliance must be connected.
        vlan_id (int): VLAN ID of the network where the helper appliance must reside.
    """

    type_: EFlrPlatformType
    host: str
    network: str
    vlan_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        host = self.host

        network = self.network

        vlan_id = self.vlan_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "host": host,
                "network": network,
                "vlanId": vlan_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EFlrPlatformType(d.pop("type"))

        host = d.pop("host")

        network = d.pop("network")

        vlan_id = d.pop("vlanId")

        hyper_v_linux_flr_helper_appliance_resource_model = cls(
            type_=type_,
            host=host,
            network=network,
            vlan_id=vlan_id,
        )

        hyper_v_linux_flr_helper_appliance_resource_model.additional_properties = d
        return hyper_v_linux_flr_helper_appliance_resource_model

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
