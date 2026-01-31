from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_authentication_model import EntraIDTenantAuthenticationModel


T = TypeVar("T", bound="EntraIDTenantModel")


@_attrs_define
class EntraIDTenantModel:
    """Entra ID tenant settings.

    Attributes:
        id (UUID): Tenant ID assigned by Veeam Backup & Replication.
        cache_repository_id (UUID): ID of a backup repository that is used as a cache repository for the tenant.
        azure_tenant_id (UUID | Unset): Tenant ID assigned by Microsoft Entra ID.
        description (str | Unset): Tenant description.
        region (EAzureRegionType | Unset): Microsoft Azure region.
        authentication (EntraIDTenantAuthenticationModel | Unset): Authentication settings.
    """

    id: UUID
    cache_repository_id: UUID
    azure_tenant_id: UUID | Unset = UNSET
    description: str | Unset = UNSET
    region: EAzureRegionType | Unset = UNSET
    authentication: EntraIDTenantAuthenticationModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        cache_repository_id = str(self.cache_repository_id)

        azure_tenant_id: str | Unset = UNSET
        if not isinstance(self.azure_tenant_id, Unset):
            azure_tenant_id = str(self.azure_tenant_id)

        description = self.description

        region: str | Unset = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.value

        authentication: dict[str, Any] | Unset = UNSET
        if not isinstance(self.authentication, Unset):
            authentication = self.authentication.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "cacheRepositoryId": cache_repository_id,
            }
        )
        if azure_tenant_id is not UNSET:
            field_dict["azureTenantId"] = azure_tenant_id
        if description is not UNSET:
            field_dict["description"] = description
        if region is not UNSET:
            field_dict["region"] = region
        if authentication is not UNSET:
            field_dict["authentication"] = authentication

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_authentication_model import EntraIDTenantAuthenticationModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        cache_repository_id = UUID(d.pop("cacheRepositoryId"))

        _azure_tenant_id = d.pop("azureTenantId", UNSET)
        azure_tenant_id: UUID | Unset
        if isinstance(_azure_tenant_id, Unset):
            azure_tenant_id = UNSET
        else:
            azure_tenant_id = UUID(_azure_tenant_id)

        description = d.pop("description", UNSET)

        _region = d.pop("region", UNSET)
        region: EAzureRegionType | Unset
        if isinstance(_region, Unset):
            region = UNSET
        else:
            region = EAzureRegionType(_region)

        _authentication = d.pop("authentication", UNSET)
        authentication: EntraIDTenantAuthenticationModel | Unset
        if isinstance(_authentication, Unset):
            authentication = UNSET
        else:
            authentication = EntraIDTenantAuthenticationModel.from_dict(_authentication)

        entra_id_tenant_model = cls(
            id=id,
            cache_repository_id=cache_repository_id,
            azure_tenant_id=azure_tenant_id,
            description=description,
            region=region,
            authentication=authentication,
        )

        entra_id_tenant_model.additional_properties = d
        return entra_id_tenant_model

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
