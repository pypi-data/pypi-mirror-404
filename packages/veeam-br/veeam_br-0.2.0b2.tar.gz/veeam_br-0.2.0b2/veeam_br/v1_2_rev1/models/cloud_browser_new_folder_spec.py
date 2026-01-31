from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType

T = TypeVar("T", bound="CloudBrowserNewFolderSpec")


@_attrs_define
class CloudBrowserNewFolderSpec:
    """
    Attributes:
        credentials_id (UUID): ID of a cloud credentials record required to connect to the object storage.
        service_type (ECloudServiceType): Type of cloud service.
        new_folder_name (str): Name of the new folder.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    new_folder_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        new_folder_name = self.new_folder_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
                "newFolderName": new_folder_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        new_folder_name = d.pop("newFolderName")

        cloud_browser_new_folder_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            new_folder_name=new_folder_name,
        )

        cloud_browser_new_folder_spec.additional_properties = d
        return cloud_browser_new_folder_spec

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
