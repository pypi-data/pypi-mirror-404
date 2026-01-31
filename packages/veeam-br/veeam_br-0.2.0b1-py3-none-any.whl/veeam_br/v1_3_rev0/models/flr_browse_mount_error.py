from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_browse_mount_error_type import EFlrBrowseMountErrorType

T = TypeVar("T", bound="FlrBrowseMountError")


@_attrs_define
class FlrBrowseMountError:
    """File-level mount error.

    Attributes:
        type_ (EFlrBrowseMountErrorType): File-level mount error type.
        message (str): File-level mount error message.
    """

    type_: EFlrBrowseMountErrorType
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EFlrBrowseMountErrorType(d.pop("type"))

        message = d.pop("message")

        flr_browse_mount_error = cls(
            type_=type_,
            message=message,
        )

        flr_browse_mount_error.additional_properties = d
        return flr_browse_mount_error

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
