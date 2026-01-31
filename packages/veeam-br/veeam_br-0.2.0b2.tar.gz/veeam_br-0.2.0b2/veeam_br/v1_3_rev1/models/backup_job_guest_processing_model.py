from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_application_aware_processing_model import BackupApplicationAwareProcessingModel
    from ..models.guest_file_system_indexing_model import GuestFileSystemIndexingModel
    from ..models.guest_interaction_proxies_settings_model import GuestInteractionProxiesSettingsModel
    from ..models.guest_os_credentials_model import GuestOsCredentialsModel


T = TypeVar("T", bound="BackupJobGuestProcessingModel")


@_attrs_define
class BackupJobGuestProcessingModel:
    """Guest processing settings.

    Attributes:
        app_aware_processing (BackupApplicationAwareProcessingModel): Application-aware processing settings.
        guest_fs_indexing (GuestFileSystemIndexingModel): VM guest OS file indexing.
        guest_interaction_proxies (GuestInteractionProxiesSettingsModel | Unset): Guest interaction proxy used to deploy
            the runtime process on the VM guest OS.
        guest_credentials (GuestOsCredentialsModel | Unset): Custom credentials.
    """

    app_aware_processing: BackupApplicationAwareProcessingModel
    guest_fs_indexing: GuestFileSystemIndexingModel
    guest_interaction_proxies: GuestInteractionProxiesSettingsModel | Unset = UNSET
    guest_credentials: GuestOsCredentialsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_aware_processing = self.app_aware_processing.to_dict()

        guest_fs_indexing = self.guest_fs_indexing.to_dict()

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
                "appAwareProcessing": app_aware_processing,
                "guestFSIndexing": guest_fs_indexing,
            }
        )
        if guest_interaction_proxies is not UNSET:
            field_dict["guestInteractionProxies"] = guest_interaction_proxies
        if guest_credentials is not UNSET:
            field_dict["guestCredentials"] = guest_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_application_aware_processing_model import BackupApplicationAwareProcessingModel
        from ..models.guest_file_system_indexing_model import GuestFileSystemIndexingModel
        from ..models.guest_interaction_proxies_settings_model import GuestInteractionProxiesSettingsModel
        from ..models.guest_os_credentials_model import GuestOsCredentialsModel

        d = dict(src_dict)
        app_aware_processing = BackupApplicationAwareProcessingModel.from_dict(d.pop("appAwareProcessing"))

        guest_fs_indexing = GuestFileSystemIndexingModel.from_dict(d.pop("guestFSIndexing"))

        _guest_interaction_proxies = d.pop("guestInteractionProxies", UNSET)
        guest_interaction_proxies: GuestInteractionProxiesSettingsModel | Unset
        if isinstance(_guest_interaction_proxies, Unset):
            guest_interaction_proxies = UNSET
        else:
            guest_interaction_proxies = GuestInteractionProxiesSettingsModel.from_dict(_guest_interaction_proxies)

        _guest_credentials = d.pop("guestCredentials", UNSET)
        guest_credentials: GuestOsCredentialsModel | Unset
        if isinstance(_guest_credentials, Unset):
            guest_credentials = UNSET
        else:
            guest_credentials = GuestOsCredentialsModel.from_dict(_guest_credentials)

        backup_job_guest_processing_model = cls(
            app_aware_processing=app_aware_processing,
            guest_fs_indexing=guest_fs_indexing,
            guest_interaction_proxies=guest_interaction_proxies,
            guest_credentials=guest_credentials,
        )

        backup_job_guest_processing_model.additional_properties = d
        return backup_job_guest_processing_model

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
