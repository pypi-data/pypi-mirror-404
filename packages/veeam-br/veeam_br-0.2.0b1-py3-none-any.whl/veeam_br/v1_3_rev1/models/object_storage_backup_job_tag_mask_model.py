from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ObjectStorageBackupJobTagMaskModel")


@_attrs_define
class ObjectStorageBackupJobTagMaskModel:
    """Tag mask for objects and prefixes in object storage.

    Attributes:
        name (str): Tag name. Note that this property is case-sensitive.
        value (str): Tag value. Note that this property is case-sensitive.
        is_object_tag (bool): If `true`, Veeam Backup & Replication will recognize the object tag. If you omit this
            parameter, the cmdlet will recognize the bucket tag. This property is required if you specify the tag for an
            individual object.
    """

    name: str
    value: str
    is_object_tag: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        value = self.value

        is_object_tag = self.is_object_tag

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "value": value,
                "isObjectTag": is_object_tag,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        value = d.pop("value")

        is_object_tag = d.pop("isObjectTag")

        object_storage_backup_job_tag_mask_model = cls(
            name=name,
            value=value,
            is_object_tag=is_object_tag,
        )

        object_storage_backup_job_tag_mask_model.additional_properties = d
        return object_storage_backup_job_tag_mask_model

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
