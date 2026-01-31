from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_cloud_credentials_import_spec import AmazonCloudCredentialsImportSpec
    from ..models.azure_compute_cloud_credentials_import_spec import AzureComputeCloudCredentialsImportSpec
    from ..models.azure_storage_cloud_credentials_import_spec import AzureStorageCloudCredentialsImportSpec
    from ..models.google_cloud_credentials_import_spec import GoogleCloudCredentialsImportSpec


T = TypeVar("T", bound="CloudCredentialsImportSpecCollection")


@_attrs_define
class CloudCredentialsImportSpecCollection:
    """Collection of settings for cloud credential import.

    Attributes:
        azure_storage (list[AzureStorageCloudCredentialsImportSpec] | Unset): Array of Azure storage accounts.
        azure_compute (list[AzureComputeCloudCredentialsImportSpec] | Unset): Array of Azure compute accounts.
        amazon (list[AmazonCloudCredentialsImportSpec] | Unset): Array of AWS accounts.
        google (list[GoogleCloudCredentialsImportSpec] | Unset): Array of Google accounts.
    """

    azure_storage: list[AzureStorageCloudCredentialsImportSpec] | Unset = UNSET
    azure_compute: list[AzureComputeCloudCredentialsImportSpec] | Unset = UNSET
    amazon: list[AmazonCloudCredentialsImportSpec] | Unset = UNSET
    google: list[GoogleCloudCredentialsImportSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_storage: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.azure_storage, Unset):
            azure_storage = []
            for azure_storage_item_data in self.azure_storage:
                azure_storage_item = azure_storage_item_data.to_dict()
                azure_storage.append(azure_storage_item)

        azure_compute: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.azure_compute, Unset):
            azure_compute = []
            for azure_compute_item_data in self.azure_compute:
                azure_compute_item = azure_compute_item_data.to_dict()
                azure_compute.append(azure_compute_item)

        amazon: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.amazon, Unset):
            amazon = []
            for amazon_item_data in self.amazon:
                amazon_item = amazon_item_data.to_dict()
                amazon.append(amazon_item)

        google: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.google, Unset):
            google = []
            for google_item_data in self.google:
                google_item = google_item_data.to_dict()
                google.append(google_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if azure_storage is not UNSET:
            field_dict["azureStorage"] = azure_storage
        if azure_compute is not UNSET:
            field_dict["azureCompute"] = azure_compute
        if amazon is not UNSET:
            field_dict["amazon"] = amazon
        if google is not UNSET:
            field_dict["google"] = google

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_cloud_credentials_import_spec import AmazonCloudCredentialsImportSpec
        from ..models.azure_compute_cloud_credentials_import_spec import AzureComputeCloudCredentialsImportSpec
        from ..models.azure_storage_cloud_credentials_import_spec import AzureStorageCloudCredentialsImportSpec
        from ..models.google_cloud_credentials_import_spec import GoogleCloudCredentialsImportSpec

        d = dict(src_dict)
        _azure_storage = d.pop("azureStorage", UNSET)
        azure_storage: list[AzureStorageCloudCredentialsImportSpec] | Unset = UNSET
        if _azure_storage is not UNSET:
            azure_storage = []
            for azure_storage_item_data in _azure_storage:
                azure_storage_item = AzureStorageCloudCredentialsImportSpec.from_dict(azure_storage_item_data)

                azure_storage.append(azure_storage_item)

        _azure_compute = d.pop("azureCompute", UNSET)
        azure_compute: list[AzureComputeCloudCredentialsImportSpec] | Unset = UNSET
        if _azure_compute is not UNSET:
            azure_compute = []
            for azure_compute_item_data in _azure_compute:
                azure_compute_item = AzureComputeCloudCredentialsImportSpec.from_dict(azure_compute_item_data)

                azure_compute.append(azure_compute_item)

        _amazon = d.pop("amazon", UNSET)
        amazon: list[AmazonCloudCredentialsImportSpec] | Unset = UNSET
        if _amazon is not UNSET:
            amazon = []
            for amazon_item_data in _amazon:
                amazon_item = AmazonCloudCredentialsImportSpec.from_dict(amazon_item_data)

                amazon.append(amazon_item)

        _google = d.pop("google", UNSET)
        google: list[GoogleCloudCredentialsImportSpec] | Unset = UNSET
        if _google is not UNSET:
            google = []
            for google_item_data in _google:
                google_item = GoogleCloudCredentialsImportSpec.from_dict(google_item_data)

                google.append(google_item)

        cloud_credentials_import_spec_collection = cls(
            azure_storage=azure_storage,
            azure_compute=azure_compute,
            amazon=amazon,
            google=google,
        )

        cloud_credentials_import_spec_collection.additional_properties = d
        return cloud_credentials_import_spec_collection

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
