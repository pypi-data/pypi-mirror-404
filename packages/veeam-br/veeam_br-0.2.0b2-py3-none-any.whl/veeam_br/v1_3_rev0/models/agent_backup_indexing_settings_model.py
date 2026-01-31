from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_object_indexing_model import AgentBackupObjectIndexingModel
    from ..models.agent_object_model import AgentObjectModel


T = TypeVar("T", bound="AgentBackupIndexingSettingsModel")


@_attrs_define
class AgentBackupIndexingSettingsModel:
    """Guest OS indexing settings.

    Attributes:
        machine_object (AgentObjectModel): Agent-managed object.
        indexing (AgentBackupObjectIndexingModel | Unset): Guest OS indexing options for the physical machine.
    """

    machine_object: AgentObjectModel
    indexing: AgentBackupObjectIndexingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        machine_object = self.machine_object.to_dict()

        indexing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.indexing, Unset):
            indexing = self.indexing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "machineObject": machine_object,
            }
        )
        if indexing is not UNSET:
            field_dict["indexing"] = indexing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_object_indexing_model import AgentBackupObjectIndexingModel
        from ..models.agent_object_model import AgentObjectModel

        d = dict(src_dict)
        machine_object = AgentObjectModel.from_dict(d.pop("machineObject"))

        _indexing = d.pop("indexing", UNSET)
        indexing: AgentBackupObjectIndexingModel | Unset
        if isinstance(_indexing, Unset):
            indexing = UNSET
        else:
            indexing = AgentBackupObjectIndexingModel.from_dict(_indexing)

        agent_backup_indexing_settings_model = cls(
            machine_object=machine_object,
            indexing=indexing,
        )

        agent_backup_indexing_settings_model.additional_properties = d
        return agent_backup_indexing_settings_model

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
