from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.smb_share_server_advanced_settings_model import SMBShareServerAdvancedSettingsModel
    from ..models.smb_share_server_processing_model import SMBShareServerProcessingModel


T = TypeVar("T", bound="SMBShareServerModel")


@_attrs_define
class SMBShareServerModel:
    """SMB share.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        path (str): UNC path to the SMB shared folder used as a backup repository.
        processing (SMBShareServerProcessingModel): SMB share processing options.
        id (UUID | Unset): ID of unstructured data server.
        name (str | Unset): DNS name of the SMB share.
        access_credentials_required (bool | Unset): If `true`, credentials are required to access the share.
        access_credentials_id (UUID | Unset): ID of the credential record used to access the share.
        advanced_settings (SMBShareServerAdvancedSettingsModel | Unset): Advanced settings for SMB share.
    """

    type_: EUnstructuredDataServerType
    path: str
    processing: SMBShareServerProcessingModel
    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    access_credentials_required: bool | Unset = UNSET
    access_credentials_id: UUID | Unset = UNSET
    advanced_settings: SMBShareServerAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        path = self.path

        processing = self.processing.to_dict()

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        access_credentials_required = self.access_credentials_required

        access_credentials_id: str | Unset = UNSET
        if not isinstance(self.access_credentials_id, Unset):
            access_credentials_id = str(self.access_credentials_id)

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "path": path,
                "processing": processing,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if access_credentials_required is not UNSET:
            field_dict["accessCredentialsRequired"] = access_credentials_required
        if access_credentials_id is not UNSET:
            field_dict["accessCredentialsId"] = access_credentials_id
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.smb_share_server_advanced_settings_model import SMBShareServerAdvancedSettingsModel
        from ..models.smb_share_server_processing_model import SMBShareServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        path = d.pop("path")

        processing = SMBShareServerProcessingModel.from_dict(d.pop("processing"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        access_credentials_required = d.pop("accessCredentialsRequired", UNSET)

        _access_credentials_id = d.pop("accessCredentialsId", UNSET)
        access_credentials_id: UUID | Unset
        if isinstance(_access_credentials_id, Unset):
            access_credentials_id = UNSET
        else:
            access_credentials_id = UUID(_access_credentials_id)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: SMBShareServerAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = SMBShareServerAdvancedSettingsModel.from_dict(_advanced_settings)

        smb_share_server_model = cls(
            type_=type_,
            path=path,
            processing=processing,
            id=id,
            name=name,
            access_credentials_required=access_credentials_required,
            access_credentials_id=access_credentials_id,
            advanced_settings=advanced_settings,
        )

        smb_share_server_model.additional_properties = d
        return smb_share_server_model

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
