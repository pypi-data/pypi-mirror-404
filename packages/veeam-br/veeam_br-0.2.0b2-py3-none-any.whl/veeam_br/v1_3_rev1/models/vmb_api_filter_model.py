from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VmbApiFilterModel")


@_attrs_define
class VmbApiFilterModel:
    """
    Attributes:
        protocol_version (int):
        assembly_version (str):
        product_id (UUID):
        version_flags (int):
    """

    protocol_version: int
    assembly_version: str
    product_id: UUID
    version_flags: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        protocol_version = self.protocol_version

        assembly_version = self.assembly_version

        product_id = str(self.product_id)

        version_flags = self.version_flags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "protocolVersion": protocol_version,
                "assemblyVersion": assembly_version,
                "productId": product_id,
                "versionFlags": version_flags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        protocol_version = d.pop("protocolVersion")

        assembly_version = d.pop("assemblyVersion")

        product_id = UUID(d.pop("productId"))

        version_flags = d.pop("versionFlags")

        vmb_api_filter_model = cls(
            protocol_version=protocol_version,
            assembly_version=assembly_version,
            product_id=product_id,
            version_flags=version_flags,
        )

        vmb_api_filter_model.additional_properties = d
        return vmb_api_filter_model

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
