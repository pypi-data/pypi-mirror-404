from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_production_item_spec import EntraIdTenantProductionItemSpec


T = TypeVar("T", bound="EntraIdTenantCheckProductionItemsSpec")


@_attrs_define
class EntraIdTenantCheckProductionItemsSpec:
    """Settings for checking if items exist in production.

    Attributes:
        items (list[EntraIdTenantProductionItemSpec]): Array of Microsoft Entra ID items that you want to check.
        credential_id (UUID | Unset): ID of the credentials used to connect to the Microsoft Entra ID tenant.
    """

    items: list[EntraIdTenantProductionItemSpec]
    credential_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        credential_id: str | Unset = UNSET
        if not isinstance(self.credential_id, Unset):
            credential_id = str(self.credential_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
            }
        )
        if credential_id is not UNSET:
            field_dict["credentialId"] = credential_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_production_item_spec import EntraIdTenantProductionItemSpec

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = EntraIdTenantProductionItemSpec.from_dict(items_item_data)

            items.append(items_item)

        _credential_id = d.pop("credentialId", UNSET)
        credential_id: UUID | Unset
        if isinstance(_credential_id, Unset):
            credential_id = UNSET
        else:
            credential_id = UUID(_credential_id)

        entra_id_tenant_check_production_items_spec = cls(
            items=items,
            credential_id=credential_id,
        )

        entra_id_tenant_check_production_items_spec.additional_properties = d
        return entra_id_tenant_check_production_items_spec

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
