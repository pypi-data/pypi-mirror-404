from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="S3CompatibleProxyModel")


@_attrs_define
class S3CompatibleProxyModel:
    """Proxy appliance for the S3 compatible storage.

    Attributes:
        managed_server_id (UUID): ID of a managed server used as a proxy appliance.
    """

    managed_server_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        managed_server_id = str(self.managed_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "managedServerId": managed_server_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        managed_server_id = UUID(d.pop("managedServerId"))

        s3_compatible_proxy_model = cls(
            managed_server_id=managed_server_id,
        )

        s3_compatible_proxy_model.additional_properties = d
        return s3_compatible_proxy_model

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
