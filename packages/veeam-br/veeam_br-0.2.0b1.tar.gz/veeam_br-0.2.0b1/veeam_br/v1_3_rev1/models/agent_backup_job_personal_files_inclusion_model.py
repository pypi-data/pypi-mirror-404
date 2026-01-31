from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupJobPersonalFilesInclusionModel")


@_attrs_define
class AgentBackupJobPersonalFilesInclusionModel:
    """Scope of personal data included in Agent backup job.

    Attributes:
        desktop (bool | Unset): If `true`, data stored in the `Desktop` folder will be included in the backup scope.
        documents (bool | Unset): If `true`, data stored in the `Documents` folder will be included in the backup scope.
        pictures (bool | Unset): If `true`, data stored in the `Pictures` folder will be included in the backup scope.
        video (bool | Unset): If `true`, data stored in the `Video` folder will be included in the backup scope.
        music (bool | Unset): If `true`, data stored in the `Music` folder will be included in the backup scope.
        favorites (bool | Unset): If `true`, data stored in the `Favorites` folder will be included in the backup scope.
        downloads (bool | Unset): If `true`, data stored in the `Downloads` folder will be included in the backup scope.
        app_data (bool | Unset): If `true`, application data will be included in the backup scope.
        other (bool | Unset): If `true`, data stored in custom locations will be included in the backup scope.
    """

    desktop: bool | Unset = UNSET
    documents: bool | Unset = UNSET
    pictures: bool | Unset = UNSET
    video: bool | Unset = UNSET
    music: bool | Unset = UNSET
    favorites: bool | Unset = UNSET
    downloads: bool | Unset = UNSET
    app_data: bool | Unset = UNSET
    other: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        desktop = self.desktop

        documents = self.documents

        pictures = self.pictures

        video = self.video

        music = self.music

        favorites = self.favorites

        downloads = self.downloads

        app_data = self.app_data

        other = self.other

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if desktop is not UNSET:
            field_dict["desktop"] = desktop
        if documents is not UNSET:
            field_dict["documents"] = documents
        if pictures is not UNSET:
            field_dict["pictures"] = pictures
        if video is not UNSET:
            field_dict["video"] = video
        if music is not UNSET:
            field_dict["music"] = music
        if favorites is not UNSET:
            field_dict["favorites"] = favorites
        if downloads is not UNSET:
            field_dict["downloads"] = downloads
        if app_data is not UNSET:
            field_dict["appData"] = app_data
        if other is not UNSET:
            field_dict["other"] = other

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        desktop = d.pop("desktop", UNSET)

        documents = d.pop("documents", UNSET)

        pictures = d.pop("pictures", UNSET)

        video = d.pop("video", UNSET)

        music = d.pop("music", UNSET)

        favorites = d.pop("favorites", UNSET)

        downloads = d.pop("downloads", UNSET)

        app_data = d.pop("appData", UNSET)

        other = d.pop("other", UNSET)

        agent_backup_job_personal_files_inclusion_model = cls(
            desktop=desktop,
            documents=documents,
            pictures=pictures,
            video=video,
            music=music,
            favorites=favorites,
            downloads=downloads,
            app_data=app_data,
            other=other,
        )

        agent_backup_job_personal_files_inclusion_model.additional_properties = d
        return agent_backup_job_personal_files_inclusion_model

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
