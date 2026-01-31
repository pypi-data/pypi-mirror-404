from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_exclusion_policy import EBackupExclusionPolicy
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupFSExclusionsModel")


@_attrs_define
class BackupFSExclusionsModel:
    """VM guest OS file exclusion.

    Attributes:
        exclusion_policy (EBackupExclusionPolicy): Exclusion policy.
        items_list (list[str] | Unset): Array of files and folders. Full paths to files and folders, environmental
            variables and file masks with the asterisk (*) and question mark (?) characters can be used.
    """

    exclusion_policy: EBackupExclusionPolicy
    items_list: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exclusion_policy = self.exclusion_policy.value

        items_list: list[str] | Unset = UNSET
        if not isinstance(self.items_list, Unset):
            items_list = self.items_list

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "exclusionPolicy": exclusion_policy,
            }
        )
        if items_list is not UNSET:
            field_dict["itemsList"] = items_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        exclusion_policy = EBackupExclusionPolicy(d.pop("exclusionPolicy"))

        items_list = cast(list[str], d.pop("itemsList", UNSET))

        backup_fs_exclusions_model = cls(
            exclusion_policy=exclusion_policy,
            items_list=items_list,
        )

        backup_fs_exclusions_model.additional_properties = d
        return backup_fs_exclusions_model

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
