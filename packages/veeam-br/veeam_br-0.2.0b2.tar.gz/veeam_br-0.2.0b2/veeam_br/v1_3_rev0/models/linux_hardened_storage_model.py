from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_hardened_repository_settings_model import LinuxHardenedRepositorySettingsModel
    from ..models.mount_servers_settings_model import MountServersSettingsModel


T = TypeVar("T", bound="LinuxHardenedStorageModel")


@_attrs_define
class LinuxHardenedStorageModel:
    """Linux hardened repository.

    Attributes:
        id (UUID): Backup repository ID.
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        host_id (UUID): ID of the server that is used as a backup repository.
        repository (LinuxHardenedRepositorySettingsModel): Repository settings.
        mount_server (MountServersSettingsModel): Mount server settings.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
    """

    id: UUID
    name: str
    description: str
    type_: ERepositoryType
    host_id: UUID
    repository: LinuxHardenedRepositorySettingsModel
    mount_server: MountServersSettingsModel
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        host_id = str(self.host_id)

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_hardened_repository_settings_model import LinuxHardenedRepositorySettingsModel
        from ..models.mount_servers_settings_model import MountServersSettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        repository = LinuxHardenedRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServersSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        linux_hardened_storage_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            host_id=host_id,
            repository=repository,
            mount_server=mount_server,
            unique_id=unique_id,
        )

        linux_hardened_storage_model.additional_properties = d
        return linux_hardened_storage_model

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
