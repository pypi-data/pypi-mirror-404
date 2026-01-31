from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobsConfirmationPrompts")


@_attrs_define
class JobsConfirmationPrompts:
    """Confirmation properties that allow you to continue to edit the job settings in specific cases.

    Attributes:
        allow_old_gfs_points_retention (bool | Unset): If `true`, modifying the GFS retention policy can remove existing
            GFS restore points.
    """

    allow_old_gfs_points_retention: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allow_old_gfs_points_retention = self.allow_old_gfs_points_retention

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if allow_old_gfs_points_retention is not UNSET:
            field_dict["allowOldGfsPointsRetention"] = allow_old_gfs_points_retention

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        allow_old_gfs_points_retention = d.pop("allowOldGfsPointsRetention", UNSET)

        jobs_confirmation_prompts = cls(
            allow_old_gfs_points_retention=allow_old_gfs_points_retention,
        )

        jobs_confirmation_prompts.additional_properties = d
        return jobs_confirmation_prompts

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
