from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupPersonalFilesExclusionModel")


@_attrs_define
class AgentBackupPersonalFilesExclusionModel:
    """Scope of personal data excluded from Agent backup job.

    Attributes:
        roaming_profiles (bool | Unset): If `true`, roaming user profiles will be excluded from the backup scope.
    """

    roaming_profiles: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        roaming_profiles = self.roaming_profiles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if roaming_profiles is not UNSET:
            field_dict["roamingProfiles"] = roaming_profiles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        roaming_profiles = d.pop("roamingProfiles", UNSET)

        agent_backup_personal_files_exclusion_model = cls(
            roaming_profiles=roaming_profiles,
        )

        agent_backup_personal_files_exclusion_model.additional_properties = d
        return agent_backup_personal_files_exclusion_model

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
