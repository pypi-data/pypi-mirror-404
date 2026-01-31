from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_retention_policy_type import EUnstructuredDataRetentionPolicyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataRetentionPolicySettingsModel")


@_attrs_define
class UnstructuredDataRetentionPolicySettingsModel:
    """Retention policy settings for unstructured data backups.

    Attributes:
        type_ (EUnstructuredDataRetentionPolicyType | Unset): Type of the retention policy.
        quantity (int | Unset): Number of days or months that you want to keep the backup in the backup repository.
    """

    type_: EUnstructuredDataRetentionPolicyType | Unset = UNSET
    quantity: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: EUnstructuredDataRetentionPolicyType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EUnstructuredDataRetentionPolicyType(_type_)

        quantity = d.pop("quantity", UNSET)

        unstructured_data_retention_policy_settings_model = cls(
            type_=type_,
            quantity=quantity,
        )

        unstructured_data_retention_policy_settings_model.additional_properties = d
        return unstructured_data_retention_policy_settings_model

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
