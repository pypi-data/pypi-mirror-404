from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_archival_type import EUnstructuredDataArchivalType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataArchiveSettingsModel")


@_attrs_define
class UnstructuredDataArchiveSettingsModel:
    """Archive settings for unstructured data backup jobs.

    Attributes:
        archival_type (EUnstructuredDataArchivalType | Unset): Filter settings for file versions that you want to keep
            on the archive repository.
        inclusion_mask (list[str] | Unset): Array of folders and files that the unstructured data backup job will save
            to the archive repository. Full paths to files and folders, environmental variables and file masks with the
            asterisk (*) and question mark (?) characters can be used.
        exclusion_mask (list[str] | Unset): Array of folders and files that the unstructured data backup job will not
            save to the archive repository. Full paths to files and folders, environmental variables and file masks with the
            asterisk (*) and question mark (?) characters can be used.
    """

    archival_type: EUnstructuredDataArchivalType | Unset = UNSET
    inclusion_mask: list[str] | Unset = UNSET
    exclusion_mask: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        archival_type: str | Unset = UNSET
        if not isinstance(self.archival_type, Unset):
            archival_type = self.archival_type.value

        inclusion_mask: list[str] | Unset = UNSET
        if not isinstance(self.inclusion_mask, Unset):
            inclusion_mask = self.inclusion_mask

        exclusion_mask: list[str] | Unset = UNSET
        if not isinstance(self.exclusion_mask, Unset):
            exclusion_mask = self.exclusion_mask

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if archival_type is not UNSET:
            field_dict["archivalType"] = archival_type
        if inclusion_mask is not UNSET:
            field_dict["inclusionMask"] = inclusion_mask
        if exclusion_mask is not UNSET:
            field_dict["exclusionMask"] = exclusion_mask

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _archival_type = d.pop("archivalType", UNSET)
        archival_type: EUnstructuredDataArchivalType | Unset
        if isinstance(_archival_type, Unset):
            archival_type = UNSET
        else:
            archival_type = EUnstructuredDataArchivalType(_archival_type)

        inclusion_mask = cast(list[str], d.pop("inclusionMask", UNSET))

        exclusion_mask = cast(list[str], d.pop("exclusionMask", UNSET))

        unstructured_data_archive_settings_model = cls(
            archival_type=archival_type,
            inclusion_mask=inclusion_mask,
            exclusion_mask=exclusion_mask,
        )

        unstructured_data_archive_settings_model.additional_properties = d
        return unstructured_data_archive_settings_model

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
