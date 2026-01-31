from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_vm_tag_model import AzureComputeVMTagModel


T = TypeVar("T", bound="AzureComputeNameModel")


@_attrs_define
class AzureComputeNameModel:
    """Name of Microsoft Azure VM.

    Attributes:
        name (str | Unset): Name of the restored Microsoft Azure VM.
        tags (list[AzureComputeVMTagModel] | Unset): Array of Microsoft Azure metadata tags that you want to assign to
            the VM.
    """

    name: str | Unset = UNSET
    tags: list[AzureComputeVMTagModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        tags: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = []
            for tags_item_data in self.tags:
                tags_item = tags_item_data.to_dict()
                tags.append(tags_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_vm_tag_model import AzureComputeVMTagModel

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: list[AzureComputeVMTagModel] | Unset = UNSET
        if _tags is not UNSET:
            tags = []
            for tags_item_data in _tags:
                tags_item = AzureComputeVMTagModel.from_dict(tags_item_data)

                tags.append(tags_item)

        azure_compute_name_model = cls(
            name=name,
            tags=tags,
        )

        azure_compute_name_model.additional_properties = d
        return azure_compute_name_model

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
