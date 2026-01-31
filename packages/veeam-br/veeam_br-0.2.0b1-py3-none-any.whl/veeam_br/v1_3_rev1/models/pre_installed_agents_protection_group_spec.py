from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.advanced_protection_group_settings_model import AdvancedProtectionGroupSettingsModel


T = TypeVar("T", bound="PreInstalledAgentsProtectionGroupSpec")


@_attrs_define
class PreInstalledAgentsProtectionGroupSpec:
    """Protection group with pre-installed agents.

    Attributes:
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        tag (str | Unset): Protection group tag.
        advanced_settings (AdvancedProtectionGroupSettingsModel | Unset): Advanced settings for the protection group.
    """

    name: str
    description: str
    type_: EProtectionGroupType
    tag: str | Unset = UNSET
    advanced_settings: AdvancedProtectionGroupSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        tag = self.tag

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
            }
        )
        if tag is not UNSET:
            field_dict["tag"] = tag
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.advanced_protection_group_settings_model import AdvancedProtectionGroupSettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        tag = d.pop("tag", UNSET)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: AdvancedProtectionGroupSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = AdvancedProtectionGroupSettingsModel.from_dict(_advanced_settings)

        pre_installed_agents_protection_group_spec = cls(
            name=name,
            description=description,
            type_=type_,
            tag=tag,
            advanced_settings=advanced_settings,
        )

        pre_installed_agents_protection_group_spec.additional_properties = d
        return pre_installed_agents_protection_group_spec

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
