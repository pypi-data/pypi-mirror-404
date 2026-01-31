from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.mount_server_model import MountServerModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="MountServerModelsResult")


@_attrs_define
class MountServerModelsResult:
    """Details on mount servers in the backup infrastructure.

    Attributes:
        data (list[MountServerModel]): Array of mount servers.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[MountServerModel]
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
        from ..models.mount_server_model import MountServerModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = MountServerModel.from_dict(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        mount_server_models_result = cls(
            data=data,
            pagination=pagination,
        )

        mount_server_models_result.additional_properties = d
        return mount_server_models_result

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
