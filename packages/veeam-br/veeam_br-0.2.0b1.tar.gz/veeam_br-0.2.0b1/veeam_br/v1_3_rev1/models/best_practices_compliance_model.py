from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_best_practice_status import EBestPracticeStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="BestPracticesComplianceModel")


@_attrs_define
class BestPracticesComplianceModel:
    """Best practice.

    Attributes:
        id (UUID): Best practice ID.
        best_practice (str): Best practice name.
        status (EBestPracticeStatus): Best practice status.
        note (str | Unset): Note that specifies the reason for suppressing the best practice compliance status
            (excluding it from the analyzer checklist).
    """

    id: UUID
    best_practice: str
    status: EBestPracticeStatus
    note: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        best_practice = self.best_practice

        status = self.status.value

        note = self.note

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bestPractice": best_practice,
                "status": status,
            }
        )
        if note is not UNSET:
            field_dict["note"] = note

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        best_practice = d.pop("bestPractice")

        status = EBestPracticeStatus(d.pop("status"))

        note = d.pop("note", UNSET)

        best_practices_compliance_model = cls(
            id=id,
            best_practice=best_practice,
            status=status,
            note=note,
        )

        best_practices_compliance_model.additional_properties = d
        return best_practices_compliance_model

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
