from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PreInstalledAgentsPackagesModel")


@_attrs_define
class PreInstalledAgentsPackagesModel:
    """Pre-installed packages on the protection group.

    Attributes:
        include (bool | Unset): If `true`, Veeam Backup & Replication will download the specified Linux or Unix
            packages.
        package_names (list[str] | Unset): Array of packages that Veeam Backup & Replication will download. To see the
            available packages, run the [Get Linux Agent Packages](Agents#operation/GetAllAgentPackages) or [Get Unix Agent
            Packages](Agents#operation/GetAllAgentPackagesForUnix) request.
    """

    include: bool | Unset = UNSET
    package_names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        include = self.include

        package_names: list[str] | Unset = UNSET
        if not isinstance(self.package_names, Unset):
            package_names = self.package_names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if include is not UNSET:
            field_dict["include"] = include
        if package_names is not UNSET:
            field_dict["packageNames"] = package_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        include = d.pop("include", UNSET)

        package_names = cast(list[str], d.pop("packageNames", UNSET))

        pre_installed_agents_packages_model = cls(
            include=include,
            package_names=package_names,
        )

        pre_installed_agents_packages_model.additional_properties = d
        return pre_installed_agents_packages_model

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
