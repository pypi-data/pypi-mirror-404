from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_flr_item_state_type import EFlrItemStateType
from ..models.e_flr_item_type import EFlrItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataFlrBrowseItemModel")


@_attrs_define
class UnstructuredDataFlrBrowseItemModel:
    """
    Attributes:
        name (str): Display name of the item.
        type_ (EFlrItemType): Item type.
        size (int): Item size in bytes.
        creation_date (datetime.datetime): Date and time when the item was created.
        modified_date (datetime.datetime): Date and time when the item was last modified.
        item_state (EFlrItemStateType): Item state.
        location (str | Unset): Item path.
    """

    name: str
    type_: EFlrItemType
    size: int
    creation_date: datetime.datetime
    modified_date: datetime.datetime
    item_state: EFlrItemStateType
    location: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        size = self.size

        creation_date = self.creation_date.isoformat()

        modified_date = self.modified_date.isoformat()

        item_state = self.item_state.value

        location = self.location

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "size": size,
                "creationDate": creation_date,
                "modifiedDate": modified_date,
                "itemState": item_state,
            }
        )
        if location is not UNSET:
            field_dict["location"] = location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        type_ = EFlrItemType(d.pop("type"))

        size = d.pop("size")

        creation_date = isoparse(d.pop("creationDate"))

        modified_date = isoparse(d.pop("modifiedDate"))

        item_state = EFlrItemStateType(d.pop("itemState"))

        location = d.pop("location", UNSET)

        unstructured_data_flr_browse_item_model = cls(
            name=name,
            type_=type_,
            size=size,
            creation_date=creation_date,
            modified_date=modified_date,
            item_state=item_state,
            location=location,
        )

        unstructured_data_flr_browse_item_model.additional_properties = d
        return unstructured_data_flr_browse_item_model

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
