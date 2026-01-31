from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_instant_restore_overwrite_mode import EUnstructuredDataInstantRestoreOverwriteMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_share_migration_destination_model import (
        UnstructuredDataShareMigrationDestinationModel,
    )
    from ..models.unstructured_data_switchover_settings_model import UnstructuredDataSwitchoverSettingsModel


T = TypeVar("T", bound="InstantUnstructuredDataRestoreMigrationSpec")


@_attrs_define
class InstantUnstructuredDataRestoreMigrationSpec:
    """Migration settings.

    Attributes:
        destination (UnstructuredDataShareMigrationDestinationModel | Unset): Migration destination for restoring
            unstructured data share.
        overwrite_mode (EUnstructuredDataInstantRestoreOverwriteMode | Unset): Overwrite mode.
        switchover_settings (UnstructuredDataSwitchoverSettingsModel | Unset): Switchover settings for Instant Recovery
            of unstructured data.
    """

    destination: UnstructuredDataShareMigrationDestinationModel | Unset = UNSET
    overwrite_mode: EUnstructuredDataInstantRestoreOverwriteMode | Unset = UNSET
    switchover_settings: UnstructuredDataSwitchoverSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        destination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.destination, Unset):
            destination = self.destination.to_dict()

        overwrite_mode: str | Unset = UNSET
        if not isinstance(self.overwrite_mode, Unset):
            overwrite_mode = self.overwrite_mode.value

        switchover_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.switchover_settings, Unset):
            switchover_settings = self.switchover_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if destination is not UNSET:
            field_dict["destination"] = destination
        if overwrite_mode is not UNSET:
            field_dict["overwriteMode"] = overwrite_mode
        if switchover_settings is not UNSET:
            field_dict["switchoverSettings"] = switchover_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_share_migration_destination_model import (
            UnstructuredDataShareMigrationDestinationModel,
        )
        from ..models.unstructured_data_switchover_settings_model import UnstructuredDataSwitchoverSettingsModel

        d = dict(src_dict)
        _destination = d.pop("destination", UNSET)
        destination: UnstructuredDataShareMigrationDestinationModel | Unset
        if isinstance(_destination, Unset):
            destination = UNSET
        else:
            destination = UnstructuredDataShareMigrationDestinationModel.from_dict(_destination)

        _overwrite_mode = d.pop("overwriteMode", UNSET)
        overwrite_mode: EUnstructuredDataInstantRestoreOverwriteMode | Unset
        if isinstance(_overwrite_mode, Unset):
            overwrite_mode = UNSET
        else:
            overwrite_mode = EUnstructuredDataInstantRestoreOverwriteMode(_overwrite_mode)

        _switchover_settings = d.pop("switchoverSettings", UNSET)
        switchover_settings: UnstructuredDataSwitchoverSettingsModel | Unset
        if isinstance(_switchover_settings, Unset):
            switchover_settings = UNSET
        else:
            switchover_settings = UnstructuredDataSwitchoverSettingsModel.from_dict(_switchover_settings)

        instant_unstructured_data_restore_migration_spec = cls(
            destination=destination,
            overwrite_mode=overwrite_mode,
            switchover_settings=switchover_settings,
        )

        instant_unstructured_data_restore_migration_spec.additional_properties = d
        return instant_unstructured_data_restore_migration_spec

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
