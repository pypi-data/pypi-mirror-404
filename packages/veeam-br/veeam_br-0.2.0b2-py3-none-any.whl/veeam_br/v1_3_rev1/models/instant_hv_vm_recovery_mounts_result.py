from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.instant_hv_vm_recovery_mount import InstantHvVMRecoveryMount
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="InstantHvVMRecoveryMountsResult")


@_attrs_define
class InstantHvVMRecoveryMountsResult:
    """Details on VM mount points.

    Attributes:
        data (list[InstantHvVMRecoveryMount]): Array of VM mount points.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[InstantHvVMRecoveryMount]
    pagination: PaginationResult
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.instant_hv_vm_recovery_mount import InstantHvVMRecoveryMount
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = InstantHvVMRecoveryMount.from_dict(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        instant_hv_vm_recovery_mounts_result = cls(
            data=data,
            pagination=pagination,
        )

        instant_hv_vm_recovery_mounts_result.additional_properties = d
        return instant_hv_vm_recovery_mounts_result

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
