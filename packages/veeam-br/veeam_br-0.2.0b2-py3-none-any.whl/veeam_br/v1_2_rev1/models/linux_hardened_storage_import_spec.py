from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType

if TYPE_CHECKING:
    from ..models.linux_hardened_repository_settings_model import LinuxHardenedRepositorySettingsModel
    from ..models.mount_server_settings_import_spec import MountServerSettingsImportSpec


T = TypeVar("T", bound="LinuxHardenedStorageImportSpec")


@_attrs_define
class LinuxHardenedStorageImportSpec:
    """
    Attributes:
        name (str): Name of the backup repository.
        description (str): Description of the backup repository.
        unique_id (str): Unique ID that identifies the backup repository.
        host_name (str): ID of the server that is used as a backup repository.
        type_ (ERepositoryType): Repository type.
        repository (LinuxHardenedRepositorySettingsModel): Repository settings.
        mount_server (MountServerSettingsImportSpec): Settings for the mount server that is used for file and
            application items restore.
    """

    name: str
    description: str
    unique_id: str
    host_name: str
    type_: ERepositoryType
    repository: LinuxHardenedRepositorySettingsModel
    mount_server: MountServerSettingsImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        unique_id = self.unique_id

        host_name = self.host_name

        type_ = self.type_.value

        repository = self.repository.to_dict()

        mount_server = self.mount_server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "uniqueId": unique_id,
                "hostName": host_name,
                "type": type_,
                "repository": repository,
                "mountServer": mount_server,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_hardened_repository_settings_model import LinuxHardenedRepositorySettingsModel
        from ..models.mount_server_settings_import_spec import MountServerSettingsImportSpec

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        unique_id = d.pop("uniqueId")

        host_name = d.pop("hostName")

        type_ = ERepositoryType(d.pop("type"))

        repository = LinuxHardenedRepositorySettingsModel.from_dict(d.pop("repository"))

        mount_server = MountServerSettingsImportSpec.from_dict(d.pop("mountServer"))

        linux_hardened_storage_import_spec = cls(
            name=name,
            description=description,
            unique_id=unique_id,
            host_name=host_name,
            type_=type_,
            repository=repository,
            mount_server=mount_server,
        )

        linux_hardened_storage_import_spec.additional_properties = d
        return linux_hardened_storage_import_spec

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
