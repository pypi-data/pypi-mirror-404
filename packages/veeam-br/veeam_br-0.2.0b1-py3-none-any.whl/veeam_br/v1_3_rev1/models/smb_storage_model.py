from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_servers_settings_model import MountServersSettingsModel
    from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
    from ..models.repository_import_options import RepositoryImportOptions
    from ..models.smb_repository_share_settings_model import SmbRepositoryShareSettingsModel


T = TypeVar("T", bound="SmbStorageModel")


@_attrs_define
class SmbStorageModel:
    """SMB backup repository.

    Attributes:
        id (UUID): Backup repository ID.
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        share (SmbRepositoryShareSettingsModel): SMB share settings.
        repository (NetworkRepositorySettingsModel): Repository settings.
        mount_server (MountServersSettingsModel): Mount server settings.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
        import_options (RepositoryImportOptions | Unset): Repository import options.
    """

    id: UUID
    name: str
    description: str
    type_: ERepositoryType
    share: SmbRepositoryShareSettingsModel
    repository: NetworkRepositorySettingsModel
    mount_server: MountServersSettingsModel
    unique_id: str | Unset = UNSET
    import_options: RepositoryImportOptions | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        share = self.share.to_dict()

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        unique_id = self.unique_id

        import_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.import_options, Unset):
            import_options = self.import_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
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
        if import_options is not UNSET:
            field_dict["importOptions"] = import_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_servers_settings_model import MountServersSettingsModel
        from ..models.network_repository_settings_model import NetworkRepositorySettingsModel
        from ..models.repository_import_options import RepositoryImportOptions
        from ..models.smb_repository_share_settings_model import SmbRepositoryShareSettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        share = SmbRepositoryShareSettingsModel.from_dict(d.pop("share"))

        repository = NetworkRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServersSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        _import_options = d.pop("importOptions", UNSET)
        import_options: RepositoryImportOptions | Unset
        if isinstance(_import_options, Unset):
            import_options = UNSET
        else:
            import_options = RepositoryImportOptions.from_dict(_import_options)

        smb_storage_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            share=share,
            repository=repository,
            mount_server=mount_server,
            unique_id=unique_id,
            import_options=import_options,
        )

        smb_storage_model.additional_properties = d
        return smb_storage_model

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
