from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_license_section_type import ELicenseSectionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseRemoveSpec")


@_attrs_define
class LicenseRemoveSpec:
    """Remove the license.

    Attributes:
        force_standalone_mode (bool | Unset): This property is only used with backup servers managed by Veeam Backup
            Enterprise Manager.<ul><li>If `true`, the request will remove the license.</li><li>If `false` or the property is
            not specified, the request will produce an error, warning you that the backup server is managed by Enterprise
            Manager.</li></ul>
        section (ELicenseSectionType | Unset): Type of the removed license.
    """

    force_standalone_mode: bool | Unset = UNSET
    section: ELicenseSectionType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        force_standalone_mode = self.force_standalone_mode

        section: str | Unset = UNSET
        if not isinstance(self.section, Unset):
            section = self.section.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if force_standalone_mode is not UNSET:
            field_dict["forceStandaloneMode"] = force_standalone_mode
        if section is not UNSET:
            field_dict["section"] = section

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        force_standalone_mode = d.pop("forceStandaloneMode", UNSET)

        _section = d.pop("section", UNSET)
        section: ELicenseSectionType | Unset
        if isinstance(_section, Unset):
            section = UNSET
        else:
            section = ELicenseSectionType(_section)

        license_remove_spec = cls(
            force_standalone_mode=force_standalone_mode,
            section=section,
        )

        license_remove_spec.additional_properties = d
        return license_remove_spec

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
