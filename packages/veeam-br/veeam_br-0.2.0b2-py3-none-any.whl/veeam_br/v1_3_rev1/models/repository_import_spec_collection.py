from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_glacier_storage_import_spec import AmazonS3GlacierStorageImportSpec
    from ..models.amazon_s3_storage_import_spec import AmazonS3StorageImportSpec
    from ..models.amazon_snowball_edge_storage_import_spec import AmazonSnowballEdgeStorageImportSpec
    from ..models.azure_archive_storage_import_spec import AzureArchiveStorageImportSpec
    from ..models.azure_blob_storage_import_spec import AzureBlobStorageImportSpec
    from ..models.azure_data_box_storage_import_spec import AzureDataBoxStorageImportSpec
    from ..models.google_cloud_storage_import_spec import GoogleCloudStorageImportSpec
    from ..models.ibm_cloud_storage_import_spec import IBMCloudStorageImportSpec
    from ..models.linux_hardened_storage_import_spec import LinuxHardenedStorageImportSpec
    from ..models.linux_local_storage_import_spec import LinuxLocalStorageImportSpec
    from ..models.nfs_storage_import_spec import NfsStorageImportSpec
    from ..models.s3_compatible_storage_import_spec import S3CompatibleStorageImportSpec
    from ..models.smb_storage_import_spec import SmbStorageImportSpec
    from ..models.wasabi_cloud_storage_import_spec import WasabiCloudStorageImportSpec
    from ..models.windows_local_storage_import_spec import WindowsLocalStorageImportSpec


T = TypeVar("T", bound="RepositoryImportSpecCollection")


@_attrs_define
class RepositoryImportSpecCollection:
    """Collection of repository import settings.

    Attributes:
        windows_local_repositories (list[WindowsLocalStorageImportSpec] | Unset): Array of Microsoft Windows-based
            repositories.
        linux_local_repositories (list[LinuxLocalStorageImportSpec] | Unset): Array of Linux-based repositories.
        smb_repositories (list[SmbStorageImportSpec] | Unset): Array of SMB backup repositories.
        nfs_repositories (list[NfsStorageImportSpec] | Unset): Array of NFS backup repositories.
        azure_blob_storages (list[AzureBlobStorageImportSpec] | Unset): Array of Microsoft Azure Blob repositories.
        azure_data_box_storages (list[AzureDataBoxStorageImportSpec] | Unset): Array of Microsoft Azure Data Box
            repositories.
        amazon_s3_storages (list[AmazonS3StorageImportSpec] | Unset): Array of Amazon S3 repositories.
        amazon_snowball_edge_storages (list[AmazonSnowballEdgeStorageImportSpec] | Unset): Array of AWS Snowball Edge
            repositories.
        s3_compatible_storages (list[S3CompatibleStorageImportSpec] | Unset): Array of S3 compatible repositories.
        google_cloud_storages (list[GoogleCloudStorageImportSpec] | Unset): Array of Google Cloud repositories.
        ibm_cloud_storages (list[IBMCloudStorageImportSpec] | Unset): Array of IBM Cloud repositories.
        amazon_s3_glacier_storages (list[AmazonS3GlacierStorageImportSpec] | Unset): Array of Amazon S3 Glacier
            repositories.
        azure_archive_storages (list[AzureArchiveStorageImportSpec] | Unset): Array of Microsoft Azure Archive
            repositories.
        wasabi_cloud_storages (list[WasabiCloudStorageImportSpec] | Unset): Array of Wasabi Cloud repositories.
        linux_hardened_repositories (list[LinuxHardenedStorageImportSpec] | Unset): Array of Linux hardened
            repositories.
    """

    windows_local_repositories: list[WindowsLocalStorageImportSpec] | Unset = UNSET
    linux_local_repositories: list[LinuxLocalStorageImportSpec] | Unset = UNSET
    smb_repositories: list[SmbStorageImportSpec] | Unset = UNSET
    nfs_repositories: list[NfsStorageImportSpec] | Unset = UNSET
    azure_blob_storages: list[AzureBlobStorageImportSpec] | Unset = UNSET
    azure_data_box_storages: list[AzureDataBoxStorageImportSpec] | Unset = UNSET
    amazon_s3_storages: list[AmazonS3StorageImportSpec] | Unset = UNSET
    amazon_snowball_edge_storages: list[AmazonSnowballEdgeStorageImportSpec] | Unset = UNSET
    s3_compatible_storages: list[S3CompatibleStorageImportSpec] | Unset = UNSET
    google_cloud_storages: list[GoogleCloudStorageImportSpec] | Unset = UNSET
    ibm_cloud_storages: list[IBMCloudStorageImportSpec] | Unset = UNSET
    amazon_s3_glacier_storages: list[AmazonS3GlacierStorageImportSpec] | Unset = UNSET
    azure_archive_storages: list[AzureArchiveStorageImportSpec] | Unset = UNSET
    wasabi_cloud_storages: list[WasabiCloudStorageImportSpec] | Unset = UNSET
    linux_hardened_repositories: list[LinuxHardenedStorageImportSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        windows_local_repositories: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.windows_local_repositories, Unset):
            windows_local_repositories = []
            for windows_local_repositories_item_data in self.windows_local_repositories:
                windows_local_repositories_item = windows_local_repositories_item_data.to_dict()
                windows_local_repositories.append(windows_local_repositories_item)

        linux_local_repositories: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.linux_local_repositories, Unset):
            linux_local_repositories = []
            for linux_local_repositories_item_data in self.linux_local_repositories:
                linux_local_repositories_item = linux_local_repositories_item_data.to_dict()
                linux_local_repositories.append(linux_local_repositories_item)

        smb_repositories: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.smb_repositories, Unset):
            smb_repositories = []
            for smb_repositories_item_data in self.smb_repositories:
                smb_repositories_item = smb_repositories_item_data.to_dict()
                smb_repositories.append(smb_repositories_item)

        nfs_repositories: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.nfs_repositories, Unset):
            nfs_repositories = []
            for nfs_repositories_item_data in self.nfs_repositories:
                nfs_repositories_item = nfs_repositories_item_data.to_dict()
                nfs_repositories.append(nfs_repositories_item)

        azure_blob_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.azure_blob_storages, Unset):
            azure_blob_storages = []
            for azure_blob_storages_item_data in self.azure_blob_storages:
                azure_blob_storages_item = azure_blob_storages_item_data.to_dict()
                azure_blob_storages.append(azure_blob_storages_item)

        azure_data_box_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.azure_data_box_storages, Unset):
            azure_data_box_storages = []
            for azure_data_box_storages_item_data in self.azure_data_box_storages:
                azure_data_box_storages_item = azure_data_box_storages_item_data.to_dict()
                azure_data_box_storages.append(azure_data_box_storages_item)

        amazon_s3_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.amazon_s3_storages, Unset):
            amazon_s3_storages = []
            for amazon_s3_storages_item_data in self.amazon_s3_storages:
                amazon_s3_storages_item = amazon_s3_storages_item_data.to_dict()
                amazon_s3_storages.append(amazon_s3_storages_item)

        amazon_snowball_edge_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.amazon_snowball_edge_storages, Unset):
            amazon_snowball_edge_storages = []
            for amazon_snowball_edge_storages_item_data in self.amazon_snowball_edge_storages:
                amazon_snowball_edge_storages_item = amazon_snowball_edge_storages_item_data.to_dict()
                amazon_snowball_edge_storages.append(amazon_snowball_edge_storages_item)

        s3_compatible_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.s3_compatible_storages, Unset):
            s3_compatible_storages = []
            for s3_compatible_storages_item_data in self.s3_compatible_storages:
                s3_compatible_storages_item = s3_compatible_storages_item_data.to_dict()
                s3_compatible_storages.append(s3_compatible_storages_item)

        google_cloud_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.google_cloud_storages, Unset):
            google_cloud_storages = []
            for google_cloud_storages_item_data in self.google_cloud_storages:
                google_cloud_storages_item = google_cloud_storages_item_data.to_dict()
                google_cloud_storages.append(google_cloud_storages_item)

        ibm_cloud_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.ibm_cloud_storages, Unset):
            ibm_cloud_storages = []
            for ibm_cloud_storages_item_data in self.ibm_cloud_storages:
                ibm_cloud_storages_item = ibm_cloud_storages_item_data.to_dict()
                ibm_cloud_storages.append(ibm_cloud_storages_item)

        amazon_s3_glacier_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.amazon_s3_glacier_storages, Unset):
            amazon_s3_glacier_storages = []
            for amazon_s3_glacier_storages_item_data in self.amazon_s3_glacier_storages:
                amazon_s3_glacier_storages_item = amazon_s3_glacier_storages_item_data.to_dict()
                amazon_s3_glacier_storages.append(amazon_s3_glacier_storages_item)

        azure_archive_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.azure_archive_storages, Unset):
            azure_archive_storages = []
            for azure_archive_storages_item_data in self.azure_archive_storages:
                azure_archive_storages_item = azure_archive_storages_item_data.to_dict()
                azure_archive_storages.append(azure_archive_storages_item)

        wasabi_cloud_storages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.wasabi_cloud_storages, Unset):
            wasabi_cloud_storages = []
            for wasabi_cloud_storages_item_data in self.wasabi_cloud_storages:
                wasabi_cloud_storages_item = wasabi_cloud_storages_item_data.to_dict()
                wasabi_cloud_storages.append(wasabi_cloud_storages_item)

        linux_hardened_repositories: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.linux_hardened_repositories, Unset):
            linux_hardened_repositories = []
            for linux_hardened_repositories_item_data in self.linux_hardened_repositories:
                linux_hardened_repositories_item = linux_hardened_repositories_item_data.to_dict()
                linux_hardened_repositories.append(linux_hardened_repositories_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if windows_local_repositories is not UNSET:
            field_dict["WindowsLocalRepositories"] = windows_local_repositories
        if linux_local_repositories is not UNSET:
            field_dict["LinuxLocalRepositories"] = linux_local_repositories
        if smb_repositories is not UNSET:
            field_dict["SmbRepositories"] = smb_repositories
        if nfs_repositories is not UNSET:
            field_dict["NfsRepositories"] = nfs_repositories
        if azure_blob_storages is not UNSET:
            field_dict["AzureBlobStorages"] = azure_blob_storages
        if azure_data_box_storages is not UNSET:
            field_dict["AzureDataBoxStorages"] = azure_data_box_storages
        if amazon_s3_storages is not UNSET:
            field_dict["AmazonS3Storages"] = amazon_s3_storages
        if amazon_snowball_edge_storages is not UNSET:
            field_dict["AmazonSnowballEdgeStorages"] = amazon_snowball_edge_storages
        if s3_compatible_storages is not UNSET:
            field_dict["S3CompatibleStorages"] = s3_compatible_storages
        if google_cloud_storages is not UNSET:
            field_dict["GoogleCloudStorages"] = google_cloud_storages
        if ibm_cloud_storages is not UNSET:
            field_dict["IBMCloudStorages"] = ibm_cloud_storages
        if amazon_s3_glacier_storages is not UNSET:
            field_dict["AmazonS3GlacierStorages"] = amazon_s3_glacier_storages
        if azure_archive_storages is not UNSET:
            field_dict["AzureArchiveStorages"] = azure_archive_storages
        if wasabi_cloud_storages is not UNSET:
            field_dict["WasabiCloudStorages"] = wasabi_cloud_storages
        if linux_hardened_repositories is not UNSET:
            field_dict["LinuxHardenedRepositories"] = linux_hardened_repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_glacier_storage_import_spec import AmazonS3GlacierStorageImportSpec
        from ..models.amazon_s3_storage_import_spec import AmazonS3StorageImportSpec
        from ..models.amazon_snowball_edge_storage_import_spec import AmazonSnowballEdgeStorageImportSpec
        from ..models.azure_archive_storage_import_spec import AzureArchiveStorageImportSpec
        from ..models.azure_blob_storage_import_spec import AzureBlobStorageImportSpec
        from ..models.azure_data_box_storage_import_spec import AzureDataBoxStorageImportSpec
        from ..models.google_cloud_storage_import_spec import GoogleCloudStorageImportSpec
        from ..models.ibm_cloud_storage_import_spec import IBMCloudStorageImportSpec
        from ..models.linux_hardened_storage_import_spec import LinuxHardenedStorageImportSpec
        from ..models.linux_local_storage_import_spec import LinuxLocalStorageImportSpec
        from ..models.nfs_storage_import_spec import NfsStorageImportSpec
        from ..models.s3_compatible_storage_import_spec import S3CompatibleStorageImportSpec
        from ..models.smb_storage_import_spec import SmbStorageImportSpec
        from ..models.wasabi_cloud_storage_import_spec import WasabiCloudStorageImportSpec
        from ..models.windows_local_storage_import_spec import WindowsLocalStorageImportSpec

        d = dict(src_dict)
        _windows_local_repositories = d.pop("WindowsLocalRepositories", UNSET)
        windows_local_repositories: list[WindowsLocalStorageImportSpec] | Unset = UNSET
        if _windows_local_repositories is not UNSET:
            windows_local_repositories = []
            for windows_local_repositories_item_data in _windows_local_repositories:
                windows_local_repositories_item = WindowsLocalStorageImportSpec.from_dict(
                    windows_local_repositories_item_data
                )

                windows_local_repositories.append(windows_local_repositories_item)

        _linux_local_repositories = d.pop("LinuxLocalRepositories", UNSET)
        linux_local_repositories: list[LinuxLocalStorageImportSpec] | Unset = UNSET
        if _linux_local_repositories is not UNSET:
            linux_local_repositories = []
            for linux_local_repositories_item_data in _linux_local_repositories:
                linux_local_repositories_item = LinuxLocalStorageImportSpec.from_dict(
                    linux_local_repositories_item_data
                )

                linux_local_repositories.append(linux_local_repositories_item)

        _smb_repositories = d.pop("SmbRepositories", UNSET)
        smb_repositories: list[SmbStorageImportSpec] | Unset = UNSET
        if _smb_repositories is not UNSET:
            smb_repositories = []
            for smb_repositories_item_data in _smb_repositories:
                smb_repositories_item = SmbStorageImportSpec.from_dict(smb_repositories_item_data)

                smb_repositories.append(smb_repositories_item)

        _nfs_repositories = d.pop("NfsRepositories", UNSET)
        nfs_repositories: list[NfsStorageImportSpec] | Unset = UNSET
        if _nfs_repositories is not UNSET:
            nfs_repositories = []
            for nfs_repositories_item_data in _nfs_repositories:
                nfs_repositories_item = NfsStorageImportSpec.from_dict(nfs_repositories_item_data)

                nfs_repositories.append(nfs_repositories_item)

        _azure_blob_storages = d.pop("AzureBlobStorages", UNSET)
        azure_blob_storages: list[AzureBlobStorageImportSpec] | Unset = UNSET
        if _azure_blob_storages is not UNSET:
            azure_blob_storages = []
            for azure_blob_storages_item_data in _azure_blob_storages:
                azure_blob_storages_item = AzureBlobStorageImportSpec.from_dict(azure_blob_storages_item_data)

                azure_blob_storages.append(azure_blob_storages_item)

        _azure_data_box_storages = d.pop("AzureDataBoxStorages", UNSET)
        azure_data_box_storages: list[AzureDataBoxStorageImportSpec] | Unset = UNSET
        if _azure_data_box_storages is not UNSET:
            azure_data_box_storages = []
            for azure_data_box_storages_item_data in _azure_data_box_storages:
                azure_data_box_storages_item = AzureDataBoxStorageImportSpec.from_dict(
                    azure_data_box_storages_item_data
                )

                azure_data_box_storages.append(azure_data_box_storages_item)

        _amazon_s3_storages = d.pop("AmazonS3Storages", UNSET)
        amazon_s3_storages: list[AmazonS3StorageImportSpec] | Unset = UNSET
        if _amazon_s3_storages is not UNSET:
            amazon_s3_storages = []
            for amazon_s3_storages_item_data in _amazon_s3_storages:
                amazon_s3_storages_item = AmazonS3StorageImportSpec.from_dict(amazon_s3_storages_item_data)

                amazon_s3_storages.append(amazon_s3_storages_item)

        _amazon_snowball_edge_storages = d.pop("AmazonSnowballEdgeStorages", UNSET)
        amazon_snowball_edge_storages: list[AmazonSnowballEdgeStorageImportSpec] | Unset = UNSET
        if _amazon_snowball_edge_storages is not UNSET:
            amazon_snowball_edge_storages = []
            for amazon_snowball_edge_storages_item_data in _amazon_snowball_edge_storages:
                amazon_snowball_edge_storages_item = AmazonSnowballEdgeStorageImportSpec.from_dict(
                    amazon_snowball_edge_storages_item_data
                )

                amazon_snowball_edge_storages.append(amazon_snowball_edge_storages_item)

        _s3_compatible_storages = d.pop("S3CompatibleStorages", UNSET)
        s3_compatible_storages: list[S3CompatibleStorageImportSpec] | Unset = UNSET
        if _s3_compatible_storages is not UNSET:
            s3_compatible_storages = []
            for s3_compatible_storages_item_data in _s3_compatible_storages:
                s3_compatible_storages_item = S3CompatibleStorageImportSpec.from_dict(s3_compatible_storages_item_data)

                s3_compatible_storages.append(s3_compatible_storages_item)

        _google_cloud_storages = d.pop("GoogleCloudStorages", UNSET)
        google_cloud_storages: list[GoogleCloudStorageImportSpec] | Unset = UNSET
        if _google_cloud_storages is not UNSET:
            google_cloud_storages = []
            for google_cloud_storages_item_data in _google_cloud_storages:
                google_cloud_storages_item = GoogleCloudStorageImportSpec.from_dict(google_cloud_storages_item_data)

                google_cloud_storages.append(google_cloud_storages_item)

        _ibm_cloud_storages = d.pop("IBMCloudStorages", UNSET)
        ibm_cloud_storages: list[IBMCloudStorageImportSpec] | Unset = UNSET
        if _ibm_cloud_storages is not UNSET:
            ibm_cloud_storages = []
            for ibm_cloud_storages_item_data in _ibm_cloud_storages:
                ibm_cloud_storages_item = IBMCloudStorageImportSpec.from_dict(ibm_cloud_storages_item_data)

                ibm_cloud_storages.append(ibm_cloud_storages_item)

        _amazon_s3_glacier_storages = d.pop("AmazonS3GlacierStorages", UNSET)
        amazon_s3_glacier_storages: list[AmazonS3GlacierStorageImportSpec] | Unset = UNSET
        if _amazon_s3_glacier_storages is not UNSET:
            amazon_s3_glacier_storages = []
            for amazon_s3_glacier_storages_item_data in _amazon_s3_glacier_storages:
                amazon_s3_glacier_storages_item = AmazonS3GlacierStorageImportSpec.from_dict(
                    amazon_s3_glacier_storages_item_data
                )

                amazon_s3_glacier_storages.append(amazon_s3_glacier_storages_item)

        _azure_archive_storages = d.pop("AzureArchiveStorages", UNSET)
        azure_archive_storages: list[AzureArchiveStorageImportSpec] | Unset = UNSET
        if _azure_archive_storages is not UNSET:
            azure_archive_storages = []
            for azure_archive_storages_item_data in _azure_archive_storages:
                azure_archive_storages_item = AzureArchiveStorageImportSpec.from_dict(azure_archive_storages_item_data)

                azure_archive_storages.append(azure_archive_storages_item)

        _wasabi_cloud_storages = d.pop("WasabiCloudStorages", UNSET)
        wasabi_cloud_storages: list[WasabiCloudStorageImportSpec] | Unset = UNSET
        if _wasabi_cloud_storages is not UNSET:
            wasabi_cloud_storages = []
            for wasabi_cloud_storages_item_data in _wasabi_cloud_storages:
                wasabi_cloud_storages_item = WasabiCloudStorageImportSpec.from_dict(wasabi_cloud_storages_item_data)

                wasabi_cloud_storages.append(wasabi_cloud_storages_item)

        _linux_hardened_repositories = d.pop("LinuxHardenedRepositories", UNSET)
        linux_hardened_repositories: list[LinuxHardenedStorageImportSpec] | Unset = UNSET
        if _linux_hardened_repositories is not UNSET:
            linux_hardened_repositories = []
            for linux_hardened_repositories_item_data in _linux_hardened_repositories:
                linux_hardened_repositories_item = LinuxHardenedStorageImportSpec.from_dict(
                    linux_hardened_repositories_item_data
                )

                linux_hardened_repositories.append(linux_hardened_repositories_item)

        repository_import_spec_collection = cls(
            windows_local_repositories=windows_local_repositories,
            linux_local_repositories=linux_local_repositories,
            smb_repositories=smb_repositories,
            nfs_repositories=nfs_repositories,
            azure_blob_storages=azure_blob_storages,
            azure_data_box_storages=azure_data_box_storages,
            amazon_s3_storages=amazon_s3_storages,
            amazon_snowball_edge_storages=amazon_snowball_edge_storages,
            s3_compatible_storages=s3_compatible_storages,
            google_cloud_storages=google_cloud_storages,
            ibm_cloud_storages=ibm_cloud_storages,
            amazon_s3_glacier_storages=amazon_s3_glacier_storages,
            azure_archive_storages=azure_archive_storages,
            wasabi_cloud_storages=wasabi_cloud_storages,
            linux_hardened_repositories=linux_hardened_repositories,
        )

        repository_import_spec_collection.additional_properties = d
        return repository_import_spec_collection

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
