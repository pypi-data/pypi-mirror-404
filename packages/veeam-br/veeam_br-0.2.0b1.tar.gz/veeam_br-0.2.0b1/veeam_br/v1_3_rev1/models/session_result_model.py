from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_session_result import ESessionResult
from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionResultModel")


@_attrs_define
class SessionResultModel:
    """Session result.

    Attributes:
        result (ESessionResult): Result status.
        message (str | Unset): Message that explains the session result.
        is_canceled (bool | Unset): If `true`, the session has been canceled.
    """

    result: ESessionResult
    message: str | Unset = UNSET
    is_canceled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = self.result.value

        message = self.message

        is_canceled = self.is_canceled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "result": result,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message
        if is_canceled is not UNSET:
            field_dict["isCanceled"] = is_canceled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        result = ESessionResult(d.pop("result"))

        message = d.pop("message", UNSET)

        is_canceled = d.pop("isCanceled", UNSET)

        session_result_model = cls(
            result=result,
            message=message,
            is_canceled=is_canceled,
        )

        session_result_model.additional_properties = d
        return session_result_model

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
