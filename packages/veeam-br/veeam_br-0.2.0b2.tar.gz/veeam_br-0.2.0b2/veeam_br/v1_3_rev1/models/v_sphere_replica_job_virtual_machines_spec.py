from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.replica_source_repositories_model import ReplicaSourceRepositoriesModel
    from ..models.v_sphere_replica_job_exclusions_spec import VSphereReplicaJobExclusionsSpec


T = TypeVar("T", bound="VSphereReplicaJobVirtualMachinesSpec")


@_attrs_define
class VSphereReplicaJobVirtualMachinesSpec:
    """Included and excluded objects.

    Attributes:
        includes (list[InventoryObjectModel]): Array of VMs and VM containers processed by the job.
        excludes (VSphereReplicaJobExclusionsSpec | Unset): Objects excluded from the job.
        source_repositories (ReplicaSourceRepositoriesModel | Unset): Source from which to obtain VM data.
    """

    includes: list[InventoryObjectModel]
    excludes: VSphereReplicaJobExclusionsSpec | Unset = UNSET
    source_repositories: ReplicaSourceRepositoriesModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        includes = []
        for includes_item_data in self.includes:
            includes_item = includes_item_data.to_dict()
            includes.append(includes_item)

        excludes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = self.excludes.to_dict()

        source_repositories: dict[str, Any] | Unset = UNSET
        if not isinstance(self.source_repositories, Unset):
            source_repositories = self.source_repositories.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes
        if source_repositories is not UNSET:
            field_dict["sourceRepositories"] = source_repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.replica_source_repositories_model import ReplicaSourceRepositoriesModel
        from ..models.v_sphere_replica_job_exclusions_spec import VSphereReplicaJobExclusionsSpec

        d = dict(src_dict)
        includes = []
        _includes = d.pop("includes")
        for includes_item_data in _includes:
            includes_item = InventoryObjectModel.from_dict(includes_item_data)

            includes.append(includes_item)

        _excludes = d.pop("excludes", UNSET)
        excludes: VSphereReplicaJobExclusionsSpec | Unset
        if isinstance(_excludes, Unset):
            excludes = UNSET
        else:
            excludes = VSphereReplicaJobExclusionsSpec.from_dict(_excludes)

        _source_repositories = d.pop("sourceRepositories", UNSET)
        source_repositories: ReplicaSourceRepositoriesModel | Unset
        if isinstance(_source_repositories, Unset):
            source_repositories = UNSET
        else:
            source_repositories = ReplicaSourceRepositoriesModel.from_dict(_source_repositories)

        v_sphere_replica_job_virtual_machines_spec = cls(
            includes=includes,
            excludes=excludes,
            source_repositories=source_repositories,
        )

        v_sphere_replica_job_virtual_machines_spec.additional_properties = d
        return v_sphere_replica_job_virtual_machines_spec

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
