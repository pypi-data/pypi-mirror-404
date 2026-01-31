from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_platform_type import EFlrPlatformType

if TYPE_CHECKING:
    from ..models.hyper_v_object_model import HyperVObjectModel


T = TypeVar("T", bound="HyperVFlrRestoreTargetHostModel")


@_attrs_define
class HyperVFlrRestoreTargetHostModel:
    """Target Microsoft Hyper-V VM for file-level restore.

    Attributes:
        type_ (EFlrPlatformType): Platform type.
        vm_object (HyperVObjectModel): Microsoft Hyper-V object.
    """

    type_: EFlrPlatformType
    vm_object: HyperVObjectModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        vm_object = self.vm_object.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "vmObject": vm_object,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_object_model import HyperVObjectModel

        d = dict(src_dict)
        type_ = EFlrPlatformType(d.pop("type"))

        vm_object = HyperVObjectModel.from_dict(d.pop("vmObject"))

        hyper_v_flr_restore_target_host_model = cls(
            type_=type_,
            vm_object=vm_object,
        )

        hyper_v_flr_restore_target_host_model.additional_properties = d
        return hyper_v_flr_restore_target_host_model

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
