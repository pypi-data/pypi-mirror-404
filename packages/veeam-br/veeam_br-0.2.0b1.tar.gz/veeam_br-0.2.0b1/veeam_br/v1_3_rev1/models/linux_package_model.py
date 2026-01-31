from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eos_bitness import EOSBitness
from ..types import UNSET, Unset

T = TypeVar("T", bound="LinuxPackageModel")


@_attrs_define
class LinuxPackageModel:
    """Linux package.

    Attributes:
        package_name (str | Unset): Linux package name.
        distribution_name (str | Unset): Linux distribution name.
        package_bitness (EOSBitness | Unset): Bitness type.
    """

    package_name: str | Unset = UNSET
    distribution_name: str | Unset = UNSET
    package_bitness: EOSBitness | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        package_name = self.package_name

        distribution_name = self.distribution_name

        package_bitness: str | Unset = UNSET
        if not isinstance(self.package_bitness, Unset):
            package_bitness = self.package_bitness.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if package_name is not UNSET:
            field_dict["packageName"] = package_name
        if distribution_name is not UNSET:
            field_dict["distributionName"] = distribution_name
        if package_bitness is not UNSET:
            field_dict["packageBitness"] = package_bitness

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        package_name = d.pop("packageName", UNSET)

        distribution_name = d.pop("distributionName", UNSET)

        _package_bitness = d.pop("packageBitness", UNSET)
        package_bitness: EOSBitness | Unset
        if isinstance(_package_bitness, Unset):
            package_bitness = UNSET
        else:
            package_bitness = EOSBitness(_package_bitness)

        linux_package_model = cls(
            package_name=package_name,
            distribution_name=distribution_name,
            package_bitness=package_bitness,
        )

        linux_package_model.additional_properties = d
        return linux_package_model

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
