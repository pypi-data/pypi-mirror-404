from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.nfs_share_server_advanced_settings_model import NFSShareServerAdvancedSettingsModel
    from ..models.nfs_share_server_processing_model import NFSShareServerProcessingModel


T = TypeVar("T", bound="NFSShareServerModel")


@_attrs_define
class NFSShareServerModel:
    """NFS share.

    Attributes:
        id (UUID): ID of the unstructured data server.
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        path (str): Path in the `server:/folder` format to the NFS file share used as a backup repository.
        processing (NFSShareServerProcessingModel): NFS share processing options.
        name (str | Unset): DNS name of the NFS share.
        advanced_settings (NFSShareServerAdvancedSettingsModel | Unset): Advanced settings for NFS share.
    """

    id: UUID
    type_: EUnstructuredDataServerType
    path: str
    processing: NFSShareServerProcessingModel
    name: str | Unset = UNSET
    advanced_settings: NFSShareServerAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        path = self.path

        processing = self.processing.to_dict()

        name = self.name

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "path": path,
                "processing": processing,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.nfs_share_server_advanced_settings_model import NFSShareServerAdvancedSettingsModel
        from ..models.nfs_share_server_processing_model import NFSShareServerProcessingModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = EUnstructuredDataServerType(d.pop("type"))

        path = d.pop("path")

        processing = NFSShareServerProcessingModel.from_dict(d.pop("processing"))

        name = d.pop("name", UNSET)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: NFSShareServerAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = NFSShareServerAdvancedSettingsModel.from_dict(_advanced_settings)

        nfs_share_server_model = cls(
            id=id,
            type_=type_,
            path=path,
            processing=processing,
            name=name,
            advanced_settings=advanced_settings,
        )

        nfs_share_server_model.additional_properties = d
        return nfs_share_server_model

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
