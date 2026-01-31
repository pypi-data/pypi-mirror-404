from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureStorageAccountInstanceSizeModel")


@_attrs_define
class AzureStorageAccountInstanceSizeModel:
    """Instance size of Microsoft Azure storage account.

    Attributes:
        cores (int | Unset): Number of cores.
        memory (int | Unset): Amount of memory in bytes.
        max_disks (int | Unset): Maximum number of disks.
        family (str | Unset): Microsoft Azure VM size family.
        name (str | Unset): Name of the Microsoft Azure VM size.
    """

    cores: int | Unset = UNSET
    memory: int | Unset = UNSET
    max_disks: int | Unset = UNSET
    family: str | Unset = UNSET
    name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cores = self.cores

        memory = self.memory

        max_disks = self.max_disks

        family = self.family

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cores is not UNSET:
            field_dict["cores"] = cores
        if memory is not UNSET:
            field_dict["memory"] = memory
        if max_disks is not UNSET:
            field_dict["maxDisks"] = max_disks
        if family is not UNSET:
            field_dict["family"] = family
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cores = d.pop("cores", UNSET)

        memory = d.pop("memory", UNSET)

        max_disks = d.pop("maxDisks", UNSET)

        family = d.pop("family", UNSET)

        name = d.pop("name", UNSET)

        azure_storage_account_instance_size_model = cls(
            cores=cores,
            memory=memory,
            max_disks=max_disks,
            family=family,
            name=name,
        )

        azure_storage_account_instance_size_model.additional_properties = d
        return azure_storage_account_instance_size_model

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
