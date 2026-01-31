from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_placement_policy_type import EPlacementPolicyType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_placement_settings_model import BackupPlacementSettingsModel


T = TypeVar("T", bound="PlacementPolicyModel")


@_attrs_define
class PlacementPolicyModel:
    """Backup file placement policy.

    Attributes:
        type_ (EPlacementPolicyType): Type of placement policy.
        settings (list[BackupPlacementSettingsModel] | Unset): Placement policy settings.
        enforce_strict_placement_policy (bool | Unset): If `true`, the backup job fails in case the placement policy
            cannot be met.
    """

    type_: EPlacementPolicyType
    settings: list[BackupPlacementSettingsModel] | Unset = UNSET
    enforce_strict_placement_policy: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        settings: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = []
            for settings_item_data in self.settings:
                settings_item = settings_item_data.to_dict()
                settings.append(settings_item)

        enforce_strict_placement_policy = self.enforce_strict_placement_policy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if settings is not UNSET:
            field_dict["settings"] = settings
        if enforce_strict_placement_policy is not UNSET:
            field_dict["enforceStrictPlacementPolicy"] = enforce_strict_placement_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_placement_settings_model import BackupPlacementSettingsModel

        d = dict(src_dict)
        type_ = EPlacementPolicyType(d.pop("type"))

        _settings = d.pop("settings", UNSET)
        settings: list[BackupPlacementSettingsModel] | Unset = UNSET
        if _settings is not UNSET:
            settings = []
            for settings_item_data in _settings:
                settings_item = BackupPlacementSettingsModel.from_dict(settings_item_data)

                settings.append(settings_item)

        enforce_strict_placement_policy = d.pop("enforceStrictPlacementPolicy", UNSET)

        placement_policy_model = cls(
            type_=type_,
            settings=settings,
            enforce_strict_placement_policy=enforce_strict_placement_policy,
        )

        placement_policy_model.additional_properties = d
        return placement_policy_model

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
