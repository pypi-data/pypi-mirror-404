from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.error_error_code import ErrorErrorCode
from ..types import UNSET, Unset

T = TypeVar("T", bound="Error")


@_attrs_define
class Error:
    """
    Attributes:
        error_code (ErrorErrorCode): The error code is a string that uniquely identifies an error condition and should
            be understood by programs that detect and handle errors by type.
        message (str): The error message contains a generic description of the error condition in English. It is
            intended for a human audience.
        resource_id (str | Unset): ID of the object that is involved in the error (or empty).
    """

    error_code: ErrorErrorCode
    message: str
    resource_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error_code = self.error_code.value

        message = self.message

        resource_id = self.resource_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "errorCode": error_code,
                "message": message,
            }
        )
        if resource_id is not UNSET:
            field_dict["resourceId"] = resource_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        error_code = ErrorErrorCode(d.pop("errorCode"))

        message = d.pop("message")

        resource_id = d.pop("resourceId", UNSET)

        error = cls(
            error_code=error_code,
            message=message,
            resource_id=resource_id,
        )

        error.additional_properties = d
        return error

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
