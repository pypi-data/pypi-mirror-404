from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_restore_overwrite_mode import EUnstructuredDataRestoreOverwriteMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="UnstructuredDataShareRestoreOptionsModel")


@_attrs_define
class UnstructuredDataShareRestoreOptionsModel:
    """Unstructured data restore options.

    Attributes:
        rollback (bool | Unset): If `true`, the bucket or container will be rolled back to the state as of a specific
            restore point.
        overwrite_mode (EUnstructuredDataRestoreOverwriteMode | Unset): Overwrite mode.
        restore_permissions (bool | Unset): If `true`, Veeam Backup & Replication will restore permissions and security
            attributes of the backups.
    """

    rollback: bool | Unset = UNSET
    overwrite_mode: EUnstructuredDataRestoreOverwriteMode | Unset = UNSET
    restore_permissions: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rollback = self.rollback

        overwrite_mode: str | Unset = UNSET
        if not isinstance(self.overwrite_mode, Unset):
            overwrite_mode = self.overwrite_mode.value

        restore_permissions = self.restore_permissions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rollback is not UNSET:
            field_dict["rollback"] = rollback
        if overwrite_mode is not UNSET:
            field_dict["overwriteMode"] = overwrite_mode
        if restore_permissions is not UNSET:
            field_dict["restorePermissions"] = restore_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rollback = d.pop("rollback", UNSET)

        _overwrite_mode = d.pop("overwriteMode", UNSET)
        overwrite_mode: EUnstructuredDataRestoreOverwriteMode | Unset
        if isinstance(_overwrite_mode, Unset):
            overwrite_mode = UNSET
        else:
            overwrite_mode = EUnstructuredDataRestoreOverwriteMode(_overwrite_mode)

        restore_permissions = d.pop("restorePermissions", UNSET)

        unstructured_data_share_restore_options_model = cls(
            rollback=rollback,
            overwrite_mode=overwrite_mode,
            restore_permissions=restore_permissions,
        )

        unstructured_data_share_restore_options_model.additional_properties = d
        return unstructured_data_share_restore_options_model

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
