from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hyper_v_volume_object_model import HyperVVolumeObjectModel


T = TypeVar("T", bound="HyperVVolumeManageModel")


@_attrs_define
class HyperVVolumeManageModel:
    """Volume properties.

    Attributes:
        volumes (list[HyperVVolumeObjectModel]): Array of volumes.
        changed_block_tracking (bool): If `true`, CBT is enabled for this host. Default: False.
        failover_to_vss_provider (bool): If `true`, Veeam Backup & Replication uses the specified hardware VSS provider
            for volume snapshot creation. Default: True.
    """

    volumes: list[HyperVVolumeObjectModel]
    changed_block_tracking: bool = False
    failover_to_vss_provider: bool = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        volumes = []
        for volumes_item_data in self.volumes:
            volumes_item = volumes_item_data.to_dict()
            volumes.append(volumes_item)

        changed_block_tracking = self.changed_block_tracking

        failover_to_vss_provider = self.failover_to_vss_provider

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "volumes": volumes,
                "changedBlockTracking": changed_block_tracking,
                "failoverToVSSProvider": failover_to_vss_provider,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_volume_object_model import HyperVVolumeObjectModel

        d = dict(src_dict)
        volumes = []
        _volumes = d.pop("volumes")
        for volumes_item_data in _volumes:
            volumes_item = HyperVVolumeObjectModel.from_dict(volumes_item_data)

            volumes.append(volumes_item)

        changed_block_tracking = d.pop("changedBlockTracking")

        failover_to_vss_provider = d.pop("failoverToVSSProvider")

        hyper_v_volume_manage_model = cls(
            volumes=volumes,
            changed_block_tracking=changed_block_tracking,
            failover_to_vss_provider=failover_to_vss_provider,
        )

        hyper_v_volume_manage_model.additional_properties = d
        return hyper_v_volume_manage_model

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
