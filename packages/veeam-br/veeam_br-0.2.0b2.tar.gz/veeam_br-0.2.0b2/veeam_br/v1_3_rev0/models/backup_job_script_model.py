from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupJobScriptModel")


@_attrs_define
class BackupJobScriptModel:
    """Paths to pre-freeze and post-thaw scripts.

    Attributes:
        pre_job_script (str | Unset): Path to the pre-freeze script.
        post_job_script (str | Unset): Path to the post-thaw script.
    """

    pre_job_script: str | Unset = UNSET
    post_job_script: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pre_job_script = self.pre_job_script

        post_job_script = self.post_job_script

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pre_job_script is not UNSET:
            field_dict["preJobScript"] = pre_job_script
        if post_job_script is not UNSET:
            field_dict["postJobScript"] = post_job_script

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pre_job_script = d.pop("preJobScript", UNSET)

        post_job_script = d.pop("postJobScript", UNSET)

        backup_job_script_model = cls(
            pre_job_script=pre_job_script,
            post_job_script=post_job_script,
        )

        backup_job_script_model.additional_properties = d
        return backup_job_script_model

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
