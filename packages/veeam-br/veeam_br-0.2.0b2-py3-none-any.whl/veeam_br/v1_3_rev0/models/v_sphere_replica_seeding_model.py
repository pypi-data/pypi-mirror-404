from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.initial_seeding_model import InitialSeedingModel
    from ..models.replica_mapping_model import ReplicaMappingModel


T = TypeVar("T", bound="VSphereReplicaSeedingModel")


@_attrs_define
class VSphereReplicaSeedingModel:
    """Replica seeding and mapping settings.

    Attributes:
        initial_seeding (InitialSeedingModel | Unset): Replica seeding settings. This option can be used if you have
            backups of the VMs that you replicate.
        replica_mapping (ReplicaMappingModel | Unset): Replica mapping settings. This option can be used if you already
            have ready-to-use copies of the source VMs in the target site.
    """

    initial_seeding: InitialSeedingModel | Unset = UNSET
    replica_mapping: ReplicaMappingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        initial_seeding: dict[str, Any] | Unset = UNSET
        if not isinstance(self.initial_seeding, Unset):
            initial_seeding = self.initial_seeding.to_dict()

        replica_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.replica_mapping, Unset):
            replica_mapping = self.replica_mapping.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if initial_seeding is not UNSET:
            field_dict["initialSeeding"] = initial_seeding
        if replica_mapping is not UNSET:
            field_dict["replicaMapping"] = replica_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.initial_seeding_model import InitialSeedingModel
        from ..models.replica_mapping_model import ReplicaMappingModel

        d = dict(src_dict)
        _initial_seeding = d.pop("initialSeeding", UNSET)
        initial_seeding: InitialSeedingModel | Unset
        if isinstance(_initial_seeding, Unset):
            initial_seeding = UNSET
        else:
            initial_seeding = InitialSeedingModel.from_dict(_initial_seeding)

        _replica_mapping = d.pop("replicaMapping", UNSET)
        replica_mapping: ReplicaMappingModel | Unset
        if isinstance(_replica_mapping, Unset):
            replica_mapping = UNSET
        else:
            replica_mapping = ReplicaMappingModel.from_dict(_replica_mapping)

        v_sphere_replica_seeding_model = cls(
            initial_seeding=initial_seeding,
            replica_mapping=replica_mapping,
        )

        v_sphere_replica_seeding_model.additional_properties = d
        return v_sphere_replica_seeding_model

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
