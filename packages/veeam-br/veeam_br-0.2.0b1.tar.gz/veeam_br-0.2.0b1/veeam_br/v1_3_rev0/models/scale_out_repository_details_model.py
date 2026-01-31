from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_scale_out_repository_extent_type import EScaleOutRepositoryExtentType

T = TypeVar("T", bound="ScaleOutRepositoryDetailsModel")


@_attrs_define
class ScaleOutRepositoryDetailsModel:
    """Details related to scale-out backup repositories.

    Attributes:
        membership (str): Scale-out backup repository to which the current repository is added as performance extent.
        scale_out_repository_id (UUID): ID of the scale-out backup repository.
        extent_type (EScaleOutRepositoryExtentType): Type of scale-out backup repository extent.
    """

    membership: str
    scale_out_repository_id: UUID
    extent_type: EScaleOutRepositoryExtentType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        membership = self.membership

        scale_out_repository_id = str(self.scale_out_repository_id)

        extent_type = self.extent_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "membership": membership,
                "scaleOutRepositoryId": scale_out_repository_id,
                "extentType": extent_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        membership = d.pop("membership")

        scale_out_repository_id = UUID(d.pop("scaleOutRepositoryId"))

        extent_type = EScaleOutRepositoryExtentType(d.pop("extentType"))

        scale_out_repository_details_model = cls(
            membership=membership,
            scale_out_repository_id=scale_out_repository_id,
            extent_type=extent_type,
        )

        scale_out_repository_details_model.additional_properties = d
        return scale_out_repository_details_model

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
