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
    """File share migration settings.

    Attributes:
        destination (UnstructuredDataShareMigrationDestinationModel): Destination for file share migration.
        switchover_settings (UnstructuredDataSwitchoverSettingsModel): Switchover settings for Instant File Share
            Recovery.
        overwrite_mode (EUnstructuredDataInstantRestoreOverwriteMode | Unset): Overwrite mode.
    """

    destination: UnstructuredDataShareMigrationDestinationModel
    switchover_settings: UnstructuredDataSwitchoverSettingsModel
    overwrite_mode: EUnstructuredDataInstantRestoreOverwriteMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        destination = self.destination.to_dict()

        switchover_settings = self.switchover_settings.to_dict()

        overwrite_mode: str | Unset = UNSET
        if not isinstance(self.overwrite_mode, Unset):
            overwrite_mode = self.overwrite_mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "destination": destination,
                "switchoverSettings": switchover_settings,
            }
        )
        if overwrite_mode is not UNSET:
            field_dict["overwriteMode"] = overwrite_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_share_migration_destination_model import (
            UnstructuredDataShareMigrationDestinationModel,
        )
        from ..models.unstructured_data_switchover_settings_model import UnstructuredDataSwitchoverSettingsModel

        d = dict(src_dict)
        destination = UnstructuredDataShareMigrationDestinationModel.from_dict(d.pop("destination"))

        switchover_settings = UnstructuredDataSwitchoverSettingsModel.from_dict(d.pop("switchoverSettings"))

        _overwrite_mode = d.pop("overwriteMode", UNSET)
        overwrite_mode: EUnstructuredDataInstantRestoreOverwriteMode | Unset
        if isinstance(_overwrite_mode, Unset):
            overwrite_mode = UNSET
        else:
            overwrite_mode = EUnstructuredDataInstantRestoreOverwriteMode(_overwrite_mode)

        instant_unstructured_data_restore_migration_spec = cls(
            destination=destination,
            switchover_settings=switchover_settings,
            overwrite_mode=overwrite_mode,
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
