from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_object_indexing_model import BackupObjectIndexingModel
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="BackupIndexingSettingsModel")


@_attrs_define
class BackupIndexingSettingsModel:
    """
    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        windows_indexing (BackupObjectIndexingModel | Unset): Guest OS indexing options for the VM.
        linux_indexing (BackupObjectIndexingModel | Unset): Guest OS indexing options for the VM.
    """

    vm_object: InventoryObjectModel
    windows_indexing: BackupObjectIndexingModel | Unset = UNSET
    linux_indexing: BackupObjectIndexingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        windows_indexing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.windows_indexing, Unset):
            windows_indexing = self.windows_indexing.to_dict()

        linux_indexing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux_indexing, Unset):
            linux_indexing = self.linux_indexing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if windows_indexing is not UNSET:
            field_dict["WindowsIndexing"] = windows_indexing
        if linux_indexing is not UNSET:
            field_dict["LinuxIndexing"] = linux_indexing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_object_indexing_model import BackupObjectIndexingModel
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        _windows_indexing = d.pop("WindowsIndexing", UNSET)
        windows_indexing: BackupObjectIndexingModel | Unset
        if isinstance(_windows_indexing, Unset):
            windows_indexing = UNSET
        else:
            windows_indexing = BackupObjectIndexingModel.from_dict(_windows_indexing)

        _linux_indexing = d.pop("LinuxIndexing", UNSET)
        linux_indexing: BackupObjectIndexingModel | Unset
        if isinstance(_linux_indexing, Unset):
            linux_indexing = UNSET
        else:
            linux_indexing = BackupObjectIndexingModel.from_dict(_linux_indexing)

        backup_indexing_settings_model = cls(
            vm_object=vm_object,
            windows_indexing=windows_indexing,
            linux_indexing=linux_indexing,
        )

        backup_indexing_settings_model.additional_properties = d
        return backup_indexing_settings_model

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
