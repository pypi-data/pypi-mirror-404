from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_copy_exclude_objects_model import BackupCopyExcludeObjectsModel
    from ..models.backup_copy_include_objects_model import BackupCopyIncludeObjectsModel


T = TypeVar("T", bound="BackupCopyJobObjectsModel")


@_attrs_define
class BackupCopyJobObjectsModel:
    """Included and excluded objects.

    Attributes:
        includes (BackupCopyIncludeObjectsModel): Included objects.
        excludes (BackupCopyExcludeObjectsModel | Unset): Excluded objects.
        enable_transaction_log_copy (bool | Unset): If `true`, backup copy job will process transaction logs of the
            source job.
    """

    includes: BackupCopyIncludeObjectsModel
    excludes: BackupCopyExcludeObjectsModel | Unset = UNSET
    enable_transaction_log_copy: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        includes = self.includes.to_dict()

        excludes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = self.excludes.to_dict()

        enable_transaction_log_copy = self.enable_transaction_log_copy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes
        if enable_transaction_log_copy is not UNSET:
            field_dict["enableTransactionLogCopy"] = enable_transaction_log_copy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_copy_exclude_objects_model import BackupCopyExcludeObjectsModel
        from ..models.backup_copy_include_objects_model import BackupCopyIncludeObjectsModel

        d = dict(src_dict)
        includes = BackupCopyIncludeObjectsModel.from_dict(d.pop("includes"))

        _excludes = d.pop("excludes", UNSET)
        excludes: BackupCopyExcludeObjectsModel | Unset
        if isinstance(_excludes, Unset):
            excludes = UNSET
        else:
            excludes = BackupCopyExcludeObjectsModel.from_dict(_excludes)

        enable_transaction_log_copy = d.pop("enableTransactionLogCopy", UNSET)

        backup_copy_job_objects_model = cls(
            includes=includes,
            excludes=excludes,
            enable_transaction_log_copy=enable_transaction_log_copy,
        )

        backup_copy_job_objects_model.additional_properties = d
        return backup_copy_job_objects_model

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
