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
    from ..models.windows_local_repository_settings_model import WindowsLocalRepositorySettingsModel


T = TypeVar("T", bound="WindowsLocalStorageSpec")


@_attrs_define
class WindowsLocalStorageSpec:
    """Microsoft Windows-based repository.

    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        host_id (UUID): ID of the server that is used as a backup repository.
        repository (WindowsLocalRepositorySettingsModel): Repository settings.
        mount_server (MountServersSettingsModel): Mount server settings.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
        import_backup (bool | Unset): If `true`, Veeam Backup & Replication will search the repository for existing
            backups and import them automatically.
        import_index (bool | Unset): If `true`, Veeam Backup & Replication will import the guest OS file system index.
    """

    name: str
    description: str
    type_: ERepositoryType
    host_id: UUID
    repository: WindowsLocalRepositorySettingsModel
    mount_server: MountServersSettingsModel
    unique_id: str | Unset = UNSET
    import_backup: bool | Unset = UNSET
    import_index: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        host_id = str(self.host_id)

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        unique_id = self.unique_id

        import_backup = self.import_backup

        import_index = self.import_index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "hostId": host_id,
                "repository": repository,
                "mountServer": mount_server,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id
        if import_backup is not UNSET:
            field_dict["importBackup"] = import_backup
        if import_index is not UNSET:
            field_dict["importIndex"] = import_index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_servers_settings_model import MountServersSettingsModel
        from ..models.windows_local_repository_settings_model import WindowsLocalRepositorySettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        repository = WindowsLocalRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServersSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        import_backup = d.pop("importBackup", UNSET)

        import_index = d.pop("importIndex", UNSET)

        windows_local_storage_spec = cls(
            name=name,
            description=description,
            type_=type_,
            host_id=host_id,
            repository=repository,
            mount_server=mount_server,
            unique_id=unique_id,
            import_backup=import_backup,
            import_index=import_index,
        )

        windows_local_storage_spec.additional_properties = d
        return windows_local_storage_spec

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
