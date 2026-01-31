from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FlrCompareAttributeModel")


@_attrs_define
class FlrCompareAttributeModel:
    """
    Attributes:
        name (str): Attribute name.
        value_backup (str): Attribute value from backup.
        value_production (str): Attribute value from production machine.
        is_changed (bool): If `true`, the item has been changed.
    """

    name: str
    value_backup: str
    value_production: str
    is_changed: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        value_backup = self.value_backup

        value_production = self.value_production

        is_changed = self.is_changed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "valueBackup": value_backup,
                "valueProduction": value_production,
                "isChanged": is_changed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        value_backup = d.pop("valueBackup")

        value_production = d.pop("valueProduction")

        is_changed = d.pop("isChanged")

        flr_compare_attribute_model = cls(
            name=name,
            value_backup=value_backup,
            value_production=value_production,
            is_changed=is_changed,
        )

        flr_compare_attribute_model.additional_properties = d
        return flr_compare_attribute_model

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
