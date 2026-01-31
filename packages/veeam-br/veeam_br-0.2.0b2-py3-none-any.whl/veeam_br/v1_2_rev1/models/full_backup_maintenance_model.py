from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.full_backup_maintenance_defragment_and_compact_model import (
        FullBackupMaintenanceDefragmentAndCompactModel,
    )
    from ..models.full_backup_maintenance_remove_data_model import FullBackupMaintenanceRemoveDataModel


T = TypeVar("T", bound="FullBackupMaintenanceModel")


@_attrs_define
class FullBackupMaintenanceModel:
    """Maintenance settings for full backup files.

    Attributes:
        remove_data (FullBackupMaintenanceRemoveDataModel | Unset): Backup data setting for deleted VMs.
        defragment_and_compact (FullBackupMaintenanceDefragmentAndCompactModel | Unset): Compact operation settings.
    """

    remove_data: FullBackupMaintenanceRemoveDataModel | Unset = UNSET
    defragment_and_compact: FullBackupMaintenanceDefragmentAndCompactModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        remove_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.remove_data, Unset):
            remove_data = self.remove_data.to_dict()

        defragment_and_compact: dict[str, Any] | Unset = UNSET
        if not isinstance(self.defragment_and_compact, Unset):
            defragment_and_compact = self.defragment_and_compact.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if remove_data is not UNSET:
            field_dict["RemoveData"] = remove_data
        if defragment_and_compact is not UNSET:
            field_dict["defragmentAndCompact"] = defragment_and_compact

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.full_backup_maintenance_defragment_and_compact_model import (
            FullBackupMaintenanceDefragmentAndCompactModel,
        )
        from ..models.full_backup_maintenance_remove_data_model import FullBackupMaintenanceRemoveDataModel

        d = dict(src_dict)
        _remove_data = d.pop("RemoveData", UNSET)
        remove_data: FullBackupMaintenanceRemoveDataModel | Unset
        if isinstance(_remove_data, Unset):
            remove_data = UNSET
        else:
            remove_data = FullBackupMaintenanceRemoveDataModel.from_dict(_remove_data)

        _defragment_and_compact = d.pop("defragmentAndCompact", UNSET)
        defragment_and_compact: FullBackupMaintenanceDefragmentAndCompactModel | Unset
        if isinstance(_defragment_and_compact, Unset):
            defragment_and_compact = UNSET
        else:
            defragment_and_compact = FullBackupMaintenanceDefragmentAndCompactModel.from_dict(_defragment_and_compact)

        full_backup_maintenance_model = cls(
            remove_data=remove_data,
            defragment_and_compact=defragment_and_compact,
        )

        full_backup_maintenance_model.additional_properties = d
        return full_backup_maintenance_model

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
