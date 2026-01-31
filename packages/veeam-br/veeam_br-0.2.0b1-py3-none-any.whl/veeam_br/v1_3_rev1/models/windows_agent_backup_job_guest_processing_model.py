from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_guest_file_system_indexing_model import AgentGuestFileSystemIndexingModel
    from ..models.windows_agent_backup_application_aware_processing_model import (
        WindowsAgentBackupApplicationAwareProcessingModel,
    )


T = TypeVar("T", bound="WindowsAgentBackupJobGuestProcessingModel")


@_attrs_define
class WindowsAgentBackupJobGuestProcessingModel:
    """Guest processing settings.

    Attributes:
        app_aware_processing (WindowsAgentBackupApplicationAwareProcessingModel | Unset): Application-aware processing
            settings.
        guest_fs_indexing (AgentGuestFileSystemIndexingModel | Unset): Guest OS file indexing.
    """

    app_aware_processing: WindowsAgentBackupApplicationAwareProcessingModel | Unset = UNSET
    guest_fs_indexing: AgentGuestFileSystemIndexingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_aware_processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.app_aware_processing, Unset):
            app_aware_processing = self.app_aware_processing.to_dict()

        guest_fs_indexing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_fs_indexing, Unset):
            guest_fs_indexing = self.guest_fs_indexing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if app_aware_processing is not UNSET:
            field_dict["appAwareProcessing"] = app_aware_processing
        if guest_fs_indexing is not UNSET:
            field_dict["guestFSIndexing"] = guest_fs_indexing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_guest_file_system_indexing_model import AgentGuestFileSystemIndexingModel
        from ..models.windows_agent_backup_application_aware_processing_model import (
            WindowsAgentBackupApplicationAwareProcessingModel,
        )

        d = dict(src_dict)
        _app_aware_processing = d.pop("appAwareProcessing", UNSET)
        app_aware_processing: WindowsAgentBackupApplicationAwareProcessingModel | Unset
        if isinstance(_app_aware_processing, Unset):
            app_aware_processing = UNSET
        else:
            app_aware_processing = WindowsAgentBackupApplicationAwareProcessingModel.from_dict(_app_aware_processing)

        _guest_fs_indexing = d.pop("guestFSIndexing", UNSET)
        guest_fs_indexing: AgentGuestFileSystemIndexingModel | Unset
        if isinstance(_guest_fs_indexing, Unset):
            guest_fs_indexing = UNSET
        else:
            guest_fs_indexing = AgentGuestFileSystemIndexingModel.from_dict(_guest_fs_indexing)

        windows_agent_backup_job_guest_processing_model = cls(
            app_aware_processing=app_aware_processing,
            guest_fs_indexing=guest_fs_indexing,
        )

        windows_agent_backup_job_guest_processing_model.additional_properties = d
        return windows_agent_backup_job_guest_processing_model

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
