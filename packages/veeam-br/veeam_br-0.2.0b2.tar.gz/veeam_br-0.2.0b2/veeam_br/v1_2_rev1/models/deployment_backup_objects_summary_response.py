from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.tenant_backup_objects_summary_response import TenantBackupObjectsSummaryResponse


T = TypeVar("T", bound="DeploymentBackupObjectsSummaryResponse")


@_attrs_define
class DeploymentBackupObjectsSummaryResponse:
    """
    Attributes:
        tenants (list[TenantBackupObjectsSummaryResponse]): Array of tenants.
    """

    tenants: list[TenantBackupObjectsSummaryResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenants = []
        for tenants_item_data in self.tenants:
            tenants_item = tenants_item_data.to_dict()
            tenants.append(tenants_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenants": tenants,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tenant_backup_objects_summary_response import TenantBackupObjectsSummaryResponse

        d = dict(src_dict)
        tenants = []
        _tenants = d.pop("tenants")
        for tenants_item_data in _tenants:
            tenants_item = TenantBackupObjectsSummaryResponse.from_dict(tenants_item_data)

            tenants.append(tenants_item)

        deployment_backup_objects_summary_response = cls(
            tenants=tenants,
        )

        deployment_backup_objects_summary_response.additional_properties = d
        return deployment_backup_objects_summary_response

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
