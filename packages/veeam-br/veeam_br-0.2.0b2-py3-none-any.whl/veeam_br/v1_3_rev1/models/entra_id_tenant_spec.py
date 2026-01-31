from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_entra_id_tenant_creation_mode import EEntraIDTenantCreationMode
from ..models.e_entra_id_tenant_resource import EEntraIdTenantResource
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_existing_account_spec import EntraIDTenantExistingAccountSpec
    from ..models.entra_id_tenant_new_account_spec import EntraIDTenantNewAccountSpec


T = TypeVar("T", bound="EntraIDTenantSpec")


@_attrs_define
class EntraIDTenantSpec:
    """Settings for Microsoft Entra ID tenant.

    Attributes:
        azure_tenant_id (UUID): Tenant ID assigned by Microsoft Entra ID.
        creation_mode (EEntraIDTenantCreationMode): Connection method that defines whether you want to connect to
            Microsoft Entra ID using an existing or a newly created app registration.
        description (str | Unset): Tenant description.
        cache_repository_id (UUID | Unset): ID of a backup repository that is used as a cache repository for the tenant.
            If you do not specify the ID, the default backup repository is used.
        region (EAzureRegionType | Unset): Microsoft Azure region.
        existing_account (EntraIDTenantExistingAccountSpec | Unset): Existing Microsoft Entra ID app registration.
        new_account (EntraIDTenantNewAccountSpec | Unset): New Microsoft Entra ID app registration.
        protection_scope (list[EEntraIdTenantResource] | Unset): Array of tenant protection scopes.
    """

    azure_tenant_id: UUID
    creation_mode: EEntraIDTenantCreationMode
    description: str | Unset = UNSET
    cache_repository_id: UUID | Unset = UNSET
    region: EAzureRegionType | Unset = UNSET
    existing_account: EntraIDTenantExistingAccountSpec | Unset = UNSET
    new_account: EntraIDTenantNewAccountSpec | Unset = UNSET
    protection_scope: list[EEntraIdTenantResource] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_tenant_id = str(self.azure_tenant_id)

        creation_mode = self.creation_mode.value

        description = self.description

        cache_repository_id: str | Unset = UNSET
        if not isinstance(self.cache_repository_id, Unset):
            cache_repository_id = str(self.cache_repository_id)

        region: str | Unset = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.value

        existing_account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.existing_account, Unset):
            existing_account = self.existing_account.to_dict()

        new_account: dict[str, Any] | Unset = UNSET
        if not isinstance(self.new_account, Unset):
            new_account = self.new_account.to_dict()

        protection_scope: list[str] | Unset = UNSET
        if not isinstance(self.protection_scope, Unset):
            protection_scope = []
            for protection_scope_item_data in self.protection_scope:
                protection_scope_item = protection_scope_item_data.value
                protection_scope.append(protection_scope_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "azureTenantId": azure_tenant_id,
                "creationMode": creation_mode,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if cache_repository_id is not UNSET:
            field_dict["cacheRepositoryId"] = cache_repository_id
        if region is not UNSET:
            field_dict["region"] = region
        if existing_account is not UNSET:
            field_dict["existingAccount"] = existing_account
        if new_account is not UNSET:
            field_dict["newAccount"] = new_account
        if protection_scope is not UNSET:
            field_dict["protectionScope"] = protection_scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_existing_account_spec import EntraIDTenantExistingAccountSpec
        from ..models.entra_id_tenant_new_account_spec import EntraIDTenantNewAccountSpec

        d = dict(src_dict)
        azure_tenant_id = UUID(d.pop("azureTenantId"))

        creation_mode = EEntraIDTenantCreationMode(d.pop("creationMode"))

        description = d.pop("description", UNSET)

        _cache_repository_id = d.pop("cacheRepositoryId", UNSET)
        cache_repository_id: UUID | Unset
        if isinstance(_cache_repository_id, Unset):
            cache_repository_id = UNSET
        else:
            cache_repository_id = UUID(_cache_repository_id)

        _region = d.pop("region", UNSET)
        region: EAzureRegionType | Unset
        if isinstance(_region, Unset):
            region = UNSET
        else:
            region = EAzureRegionType(_region)

        _existing_account = d.pop("existingAccount", UNSET)
        existing_account: EntraIDTenantExistingAccountSpec | Unset
        if isinstance(_existing_account, Unset):
            existing_account = UNSET
        else:
            existing_account = EntraIDTenantExistingAccountSpec.from_dict(_existing_account)

        _new_account = d.pop("newAccount", UNSET)
        new_account: EntraIDTenantNewAccountSpec | Unset
        if isinstance(_new_account, Unset):
            new_account = UNSET
        else:
            new_account = EntraIDTenantNewAccountSpec.from_dict(_new_account)

        _protection_scope = d.pop("protectionScope", UNSET)
        protection_scope: list[EEntraIdTenantResource] | Unset = UNSET
        if _protection_scope is not UNSET:
            protection_scope = []
            for protection_scope_item_data in _protection_scope:
                protection_scope_item = EEntraIdTenantResource(protection_scope_item_data)

                protection_scope.append(protection_scope_item)

        entra_id_tenant_spec = cls(
            azure_tenant_id=azure_tenant_id,
            creation_mode=creation_mode,
            description=description,
            cache_repository_id=cache_repository_id,
            region=region,
            existing_account=existing_account,
            new_account=new_account,
            protection_scope=protection_scope,
        )

        entra_id_tenant_spec.additional_properties = d
        return entra_id_tenant_spec

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
