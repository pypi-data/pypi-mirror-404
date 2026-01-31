from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.archive_tier_model import ArchiveTierModel
    from ..models.capacity_tier_model import CapacityTierModel
    from ..models.performance_tier_spec import PerformanceTierSpec
    from ..models.placement_policy_model import PlacementPolicyModel


T = TypeVar("T", bound="ScaleOutRepositorySpec")


@_attrs_define
class ScaleOutRepositorySpec:
    """
    Attributes:
        name (str): Name of the scale-out backup repository.
        description (str): Description of the scale-out backup repository.
        performance_tier (PerformanceTierSpec): Performance tier.
        unique_id (str | Unset): Unique ID assigned to the scale-out backup repository.
        placement_policy (PlacementPolicyModel | Unset): Backup file placement policy.
        capacity_tier (CapacityTierModel | Unset): Capacity tier.
        archive_tier (ArchiveTierModel | Unset): Archive tier.
    """

    name: str
    description: str
    performance_tier: PerformanceTierSpec
    unique_id: str | Unset = UNSET
    placement_policy: PlacementPolicyModel | Unset = UNSET
    capacity_tier: CapacityTierModel | Unset = UNSET
    archive_tier: ArchiveTierModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        performance_tier = self.performance_tier.to_dict()

        unique_id = self.unique_id

        placement_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.placement_policy, Unset):
            placement_policy = self.placement_policy.to_dict()

        capacity_tier: dict[str, Any] | Unset = UNSET
        if not isinstance(self.capacity_tier, Unset):
            capacity_tier = self.capacity_tier.to_dict()

        archive_tier: dict[str, Any] | Unset = UNSET
        if not isinstance(self.archive_tier, Unset):
            archive_tier = self.archive_tier.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "performanceTier": performance_tier,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id
        if placement_policy is not UNSET:
            field_dict["placementPolicy"] = placement_policy
        if capacity_tier is not UNSET:
            field_dict["capacityTier"] = capacity_tier
        if archive_tier is not UNSET:
            field_dict["archiveTier"] = archive_tier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.archive_tier_model import ArchiveTierModel
        from ..models.capacity_tier_model import CapacityTierModel
        from ..models.performance_tier_spec import PerformanceTierSpec
        from ..models.placement_policy_model import PlacementPolicyModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        performance_tier = PerformanceTierSpec.from_dict(d.pop("performanceTier"))

        unique_id = d.pop("uniqueId", UNSET)

        _placement_policy = d.pop("placementPolicy", UNSET)
        placement_policy: PlacementPolicyModel | Unset
        if isinstance(_placement_policy, Unset):
            placement_policy = UNSET
        else:
            placement_policy = PlacementPolicyModel.from_dict(_placement_policy)

        _capacity_tier = d.pop("capacityTier", UNSET)
        capacity_tier: CapacityTierModel | Unset
        if isinstance(_capacity_tier, Unset):
            capacity_tier = UNSET
        else:
            capacity_tier = CapacityTierModel.from_dict(_capacity_tier)

        _archive_tier = d.pop("archiveTier", UNSET)
        archive_tier: ArchiveTierModel | Unset
        if isinstance(_archive_tier, Unset):
            archive_tier = UNSET
        else:
            archive_tier = ArchiveTierModel.from_dict(_archive_tier)

        scale_out_repository_spec = cls(
            name=name,
            description=description,
            performance_tier=performance_tier,
            unique_id=unique_id,
            placement_policy=placement_policy,
            capacity_tier=capacity_tier,
            archive_tier=archive_tier,
        )

        scale_out_repository_spec.additional_properties = d
        return scale_out_repository_spec

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
