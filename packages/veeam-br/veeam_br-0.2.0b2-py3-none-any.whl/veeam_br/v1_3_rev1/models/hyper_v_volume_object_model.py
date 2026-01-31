from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.volume_settings_model import VolumeSettingsModel


T = TypeVar("T", bound="HyperVVolumeObjectModel")


@_attrs_define
class HyperVVolumeObjectModel:
    """Volume object properties.

    Attributes:
        volume (InventoryObjectModel): Inventory object properties.
        volume_settings (VolumeSettingsModel): Settings for Microsoft Hyper-V volume.
    """

    volume: InventoryObjectModel
    volume_settings: VolumeSettingsModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        volume = self.volume.to_dict()

        volume_settings = self.volume_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "volume": volume,
                "volumeSettings": volume_settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.volume_settings_model import VolumeSettingsModel

        d = dict(src_dict)
        volume = InventoryObjectModel.from_dict(d.pop("volume"))

        volume_settings = VolumeSettingsModel.from_dict(d.pop("volumeSettings"))

        hyper_v_volume_object_model = cls(
            volume=volume,
            volume_settings=volume_settings,
        )

        hyper_v_volume_object_model.additional_properties = d
        return hyper_v_volume_object_model

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
