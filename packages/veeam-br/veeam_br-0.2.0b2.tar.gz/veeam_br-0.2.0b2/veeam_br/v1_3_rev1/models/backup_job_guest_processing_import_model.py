from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_application_aware_processing_import_model import BackupApplicationAwareProcessingImportModel
    from ..models.guest_file_system_indexing_model import GuestFileSystemIndexingModel
    from ..models.guest_interaction_proxies_settings_import_model import GuestInteractionProxiesSettingsImportModel
    from ..models.guest_os_credentials_import_model import GuestOsCredentialsImportModel


T = TypeVar("T", bound="BackupJobGuestProcessingImportModel")


@_attrs_define
class BackupJobGuestProcessingImportModel:
    """Guest processing settings.

    Attributes:
        application_aware_processing (BackupApplicationAwareProcessingImportModel): Application-aware processing
            settings.
        guest_file_system_indexing (GuestFileSystemIndexingModel): VM guest OS file indexing.
        guest_interaction_proxies (GuestInteractionProxiesSettingsImportModel | Unset): Guest interaction proxy used to
            deploy the runtime process on the VM guest OS.
        guest_credentials (GuestOsCredentialsImportModel | Unset): VM custom credentials.
    """

    application_aware_processing: BackupApplicationAwareProcessingImportModel
    guest_file_system_indexing: GuestFileSystemIndexingModel
    guest_interaction_proxies: GuestInteractionProxiesSettingsImportModel | Unset = UNSET
    guest_credentials: GuestOsCredentialsImportModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        application_aware_processing = self.application_aware_processing.to_dict()

        guest_file_system_indexing = self.guest_file_system_indexing.to_dict()

        guest_interaction_proxies: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_interaction_proxies, Unset):
            guest_interaction_proxies = self.guest_interaction_proxies.to_dict()

        guest_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_credentials, Unset):
            guest_credentials = self.guest_credentials.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "applicationAwareProcessing": application_aware_processing,
                "guestFileSystemIndexing": guest_file_system_indexing,
            }
        )
        if guest_interaction_proxies is not UNSET:
            field_dict["guestInteractionProxies"] = guest_interaction_proxies
        if guest_credentials is not UNSET:
            field_dict["guestCredentials"] = guest_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_application_aware_processing_import_model import (
            BackupApplicationAwareProcessingImportModel,
        )
        from ..models.guest_file_system_indexing_model import GuestFileSystemIndexingModel
        from ..models.guest_interaction_proxies_settings_import_model import GuestInteractionProxiesSettingsImportModel
        from ..models.guest_os_credentials_import_model import GuestOsCredentialsImportModel

        d = dict(src_dict)
        application_aware_processing = BackupApplicationAwareProcessingImportModel.from_dict(
            d.pop("applicationAwareProcessing")
        )

        guest_file_system_indexing = GuestFileSystemIndexingModel.from_dict(d.pop("guestFileSystemIndexing"))

        _guest_interaction_proxies = d.pop("guestInteractionProxies", UNSET)
        guest_interaction_proxies: GuestInteractionProxiesSettingsImportModel | Unset
        if isinstance(_guest_interaction_proxies, Unset):
            guest_interaction_proxies = UNSET
        else:
            guest_interaction_proxies = GuestInteractionProxiesSettingsImportModel.from_dict(_guest_interaction_proxies)

        _guest_credentials = d.pop("guestCredentials", UNSET)
        guest_credentials: GuestOsCredentialsImportModel | Unset
        if isinstance(_guest_credentials, Unset):
            guest_credentials = UNSET
        else:
            guest_credentials = GuestOsCredentialsImportModel.from_dict(_guest_credentials)

        backup_job_guest_processing_import_model = cls(
            application_aware_processing=application_aware_processing,
            guest_file_system_indexing=guest_file_system_indexing,
            guest_interaction_proxies=guest_interaction_proxies,
            guest_credentials=guest_credentials,
        )

        backup_job_guest_processing_import_model.additional_properties = d
        return backup_job_guest_processing_import_model

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
