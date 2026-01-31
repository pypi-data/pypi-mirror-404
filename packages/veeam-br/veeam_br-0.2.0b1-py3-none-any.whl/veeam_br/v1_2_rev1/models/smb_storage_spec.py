from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_server_settings_model import MountServerSettingsModel
    from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
    from ..models.smb_repository_share_settings_model import SmbRepositoryShareSettingsModel


T = TypeVar("T", bound="SmbStorageSpec")


@_attrs_define
class SmbStorageSpec:
    """SMB backup repository.

    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        share (SmbRepositoryShareSettingsModel): Share settings.
        repository (NetworkRepositorySettingsModel): Repository settings.
        mount_server (MountServerSettingsModel): Settings for the mount server that is used for file and application
            items restore.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
    """

    name: str
    description: str
    type_: ERepositoryType
    share: SmbRepositoryShareSettingsModel
    repository: NetworkRepositorySettingsModel
    mount_server: MountServerSettingsModel
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        share = self.share.to_dict()

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "share": share,
                "repository": repository,
                "mountServer": mount_server,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_server_settings_model import MountServerSettingsModel
        from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
        from ..models.smb_repository_share_settings_model import SmbRepositoryShareSettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        share = SmbRepositoryShareSettingsModel.from_dict(d.pop("share"))

        repository = NetworkRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServerSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        smb_storage_spec = cls(
            name=name,
            description=description,
            type_=type_,
            share=share,
            repository=repository,
            mount_server=mount_server,
            unique_id=unique_id,
        )

        smb_storage_spec.additional_properties = d
        return smb_storage_spec

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
