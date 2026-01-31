from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.v_sphere_replica_job_advanced_settings_model import VSphereReplicaJobAdvancedSettingsModel


T = TypeVar("T", bound="VSphereReplicaJobSettingsModel")


@_attrs_define
class VSphereReplicaJobSettingsModel:
    """Replication job settings.

    Attributes:
        metadata_repository_id (UUID): ID of a backup repository that stores replica metadata.
        replica_name_suffix (str): Suffix added to source VM names.
        restore_points_to_keep (int): Number of restore points that the replication job must maintain. The maximum
            number is limited to 28.
        advanced_settings (VSphereReplicaJobAdvancedSettingsModel | Unset): Advanced job settings.
    """

    metadata_repository_id: UUID
    replica_name_suffix: str
    restore_points_to_keep: int
    advanced_settings: VSphereReplicaJobAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata_repository_id = str(self.metadata_repository_id)

        replica_name_suffix = self.replica_name_suffix

        restore_points_to_keep = self.restore_points_to_keep

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metadataRepositoryId": metadata_repository_id,
                "replicaNameSuffix": replica_name_suffix,
                "restorePointsToKeep": restore_points_to_keep,
            }
        )
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v_sphere_replica_job_advanced_settings_model import VSphereReplicaJobAdvancedSettingsModel

        d = dict(src_dict)
        metadata_repository_id = UUID(d.pop("metadataRepositoryId"))

        replica_name_suffix = d.pop("replicaNameSuffix")

        restore_points_to_keep = d.pop("restorePointsToKeep")

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: VSphereReplicaJobAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = VSphereReplicaJobAdvancedSettingsModel.from_dict(_advanced_settings)

        v_sphere_replica_job_settings_model = cls(
            metadata_repository_id=metadata_repository_id,
            replica_name_suffix=replica_name_suffix,
            restore_points_to_keep=restore_points_to_keep,
            advanced_settings=advanced_settings,
        )

        v_sphere_replica_job_settings_model.additional_properties = d
        return v_sphere_replica_job_settings_model

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
