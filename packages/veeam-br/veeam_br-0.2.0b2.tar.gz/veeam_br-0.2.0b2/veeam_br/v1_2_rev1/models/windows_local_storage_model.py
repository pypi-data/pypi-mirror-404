from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_server_settings_model import MountServerSettingsModel
    from ..models.windows_local_repository_settings_model import WindowsLocalRepositorySettingsModel


T = TypeVar("T", bound="WindowsLocalStorageModel")


@_attrs_define
class WindowsLocalStorageModel:
    """Microsoft Windows-based repository.

    Attributes:
        id (UUID): ID of the backup repository.
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        type_ (ERepositoryType): Repository type.
        host_id (UUID): ID of the server that is used as a backup repository.
        repository (WindowsLocalRepositorySettingsModel): Repository settings.
        mount_server (MountServerSettingsModel): Settings for the mount server that is used for file and application
            items restore.
        unique_id (str | Unset): Unique ID that identifies the backup repository.
    """

    id: UUID
    name: str
    description: str
    type_: ERepositoryType
    host_id: UUID
    repository: WindowsLocalRepositorySettingsModel
    mount_server: MountServerSettingsModel
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
        from ..models.mount_server_settings_model import MountServerSettingsModel
        from ..models.windows_local_repository_settings_model import WindowsLocalRepositorySettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = ERepositoryType(d.pop("type"))

        host_id = UUID(d.pop("hostId"))

        repository = WindowsLocalRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServerSettingsModel.from_dict(d.pop("mountServer"))

        unique_id = d.pop("uniqueId", UNSET)

        windows_local_storage_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            host_id=host_id,
            repository=repository,
            mount_server=mount_server,
            unique_id=unique_id,
        )

        windows_local_storage_model.additional_properties = d
        return windows_local_storage_model

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
