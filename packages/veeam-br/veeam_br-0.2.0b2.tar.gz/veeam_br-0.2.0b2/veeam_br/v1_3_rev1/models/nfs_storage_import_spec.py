from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType

if TYPE_CHECKING:
    from ..models.mount_servers_settings_import_spec import MountServersSettingsImportSpec
    from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
    from ..models.nfs_repository_share_settings_spec import NfsRepositoryShareSettingsSpec


T = TypeVar("T", bound="NfsStorageImportSpec")


@_attrs_define
class NfsStorageImportSpec:
    """Import settings for NFS shares.

    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        unique_id (str): Unique ID that identifies the backup repository.
        type_ (ERepositoryType): Repository type.
        share (NfsRepositoryShareSettingsSpec): NFS share settings.
        repository (NetworkRepositorySettingsModel): Repository settings.
        mount_server (MountServersSettingsImportSpec): Import settings for mount servers.
    """

    name: str
    description: str
    unique_id: str
    type_: ERepositoryType
    share: NfsRepositoryShareSettingsSpec
    repository: NetworkRepositorySettingsModel
    mount_server: MountServersSettingsImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        type_ = self.type_.value

        share = self.share.to_dict()

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "uniqueId": unique_id,
                "type": type_,
                "share": share,
                "repository": repository,
                "mountServer": mount_server,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_servers_settings_import_spec import MountServersSettingsImportSpec
        from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
        from ..models.nfs_repository_share_settings_spec import NfsRepositoryShareSettingsSpec

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        type_ = ERepositoryType(d.pop("type"))

        share = NfsRepositoryShareSettingsSpec.from_dict(d.pop("share"))

        repository = NetworkRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServersSettingsImportSpec.from_dict(d.pop("mountServer"))

        nfs_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            type_=type_,
            share=share,
            repository=repository,
            mount_server=mount_server,
        )

        nfs_storage_import_spec.additional_properties = d
        return nfs_storage_import_spec

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
