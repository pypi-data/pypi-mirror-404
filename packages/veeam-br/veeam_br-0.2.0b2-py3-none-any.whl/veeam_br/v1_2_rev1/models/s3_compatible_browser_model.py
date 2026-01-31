from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.s3_compatible_region_browser_model import S3CompatibleRegionBrowserModel


T = TypeVar("T", bound="S3CompatibleBrowserModel")


@_attrs_define
class S3CompatibleBrowserModel:
    """
    Attributes:
        credentials_id (UUID): ID of the cloud credentials record.
        service_type (ECloudServiceType): Type of cloud service.
        host_id (UUID | Unset): ID of a server used to connect to the S3 compatible storage.
        connection_point (str | Unset): Service point address and port number of the S3 compatible storage.
        regions (list[S3CompatibleRegionBrowserModel] | Unset): Array of regions.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    host_id: UUID | Unset = UNSET
    connection_point: str | Unset = UNSET
    regions: list[S3CompatibleRegionBrowserModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        host_id: str | Unset = UNSET
        if not isinstance(self.host_id, Unset):
            host_id = str(self.host_id)

        connection_point = self.connection_point

        regions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.regions, Unset):
            regions = []
            for regions_item_data in self.regions:
                regions_item = regions_item_data.to_dict()
                regions.append(regions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
            }
        )
        if host_id is not UNSET:
            field_dict["hostId"] = host_id
        if connection_point is not UNSET:
            field_dict["connectionPoint"] = connection_point
        if regions is not UNSET:
            field_dict["regions"] = regions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.s3_compatible_region_browser_model import S3CompatibleRegionBrowserModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        _host_id = d.pop("hostId", UNSET)
        host_id: UUID | Unset
        if isinstance(_host_id, Unset):
            host_id = UNSET
        else:
            host_id = UUID(_host_id)

        connection_point = d.pop("connectionPoint", UNSET)

        _regions = d.pop("regions", UNSET)
        regions: list[S3CompatibleRegionBrowserModel] | Unset = UNSET
        if _regions is not UNSET:
            regions = []
            for regions_item_data in _regions:
                regions_item = S3CompatibleRegionBrowserModel.from_dict(regions_item_data)

                regions.append(regions_item)

        s3_compatible_browser_model = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            host_id=host_id,
            connection_point=connection_point,
            regions=regions,
        )

        s3_compatible_browser_model.additional_properties = d
        return s3_compatible_browser_model

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
