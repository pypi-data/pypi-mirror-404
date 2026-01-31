from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.v_sphere_replica_job_destination_mapping_model import VSphereReplicaJobDestinationMappingModel


T = TypeVar("T", bound="VSphereReplicaJobDestinationModel")


@_attrs_define
class VSphereReplicaJobDestinationModel:
    """Replica destination&#58; target host or cluster, target resource pool, target folder, target datastore and mapping
    rules.

        Attributes:
            host (InventoryObjectModel): Inventory object properties.
            resource_pool (InventoryObjectModel): Inventory object properties.
            folder (InventoryObjectModel): Inventory object properties.
            datastore (InventoryObjectModel): Inventory object properties.
            mapping_rules (list[VSphereReplicaJobDestinationMappingModel] | Unset): Mapping rules that define files location
                and disk provisioning types for replica VMs.<ul><li>`vmObject` — VM that you customize files location
                for.</li><li>`configurationFilesDatastoreMapping` — Datastore for replica configuration
                files.</li><li>`diskFilesMapping` — Mapping rules for VM disks.</li></ul>
    """

    host: InventoryObjectModel
    resource_pool: InventoryObjectModel
    folder: InventoryObjectModel
    datastore: InventoryObjectModel
    mapping_rules: list[VSphereReplicaJobDestinationMappingModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host = self.host.to_dict()

        resource_pool = self.resource_pool.to_dict()

        folder = self.folder.to_dict()

        datastore = self.datastore.to_dict()

        mapping_rules: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.mapping_rules, Unset):
            mapping_rules = []
            for mapping_rules_item_data in self.mapping_rules:
                mapping_rules_item = mapping_rules_item_data.to_dict()
                mapping_rules.append(mapping_rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "host": host,
                "resourcePool": resource_pool,
                "folder": folder,
                "datastore": datastore,
            }
        )
        if mapping_rules is not UNSET:
            field_dict["mappingRules"] = mapping_rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.v_sphere_replica_job_destination_mapping_model import VSphereReplicaJobDestinationMappingModel

        d = dict(src_dict)
        host = InventoryObjectModel.from_dict(d.pop("host"))

        resource_pool = InventoryObjectModel.from_dict(d.pop("resourcePool"))

        folder = InventoryObjectModel.from_dict(d.pop("folder"))

        datastore = InventoryObjectModel.from_dict(d.pop("datastore"))

        _mapping_rules = d.pop("mappingRules", UNSET)
        mapping_rules: list[VSphereReplicaJobDestinationMappingModel] | Unset = UNSET
        if _mapping_rules is not UNSET:
            mapping_rules = []
            for mapping_rules_item_data in _mapping_rules:
                mapping_rules_item = VSphereReplicaJobDestinationMappingModel.from_dict(mapping_rules_item_data)

                mapping_rules.append(mapping_rules_item)

        v_sphere_replica_job_destination_model = cls(
            host=host,
            resource_pool=resource_pool,
            folder=folder,
            datastore=datastore,
            mapping_rules=mapping_rules,
        )

        v_sphere_replica_job_destination_model.additional_properties = d
        return v_sphere_replica_job_destination_model

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
