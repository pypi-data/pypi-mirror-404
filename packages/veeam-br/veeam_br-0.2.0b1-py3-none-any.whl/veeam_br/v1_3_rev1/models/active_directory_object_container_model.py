from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.ad_domain_model import ADDomainModel
    from ..models.ad_object_model import ADObjectModel


T = TypeVar("T", bound="ActiveDirectoryObjectContainerModel")


@_attrs_define
class ActiveDirectoryObjectContainerModel:
    """Active Directory container.

    Attributes:
        domain_controller_settings (ADDomainModel): Settings of Active Directory domain.
        objects (list[ADObjectModel]): Array of Active Directory objects.
    """

    domain_controller_settings: ADDomainModel
    objects: list[ADObjectModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain_controller_settings = self.domain_controller_settings.to_dict()

        objects = []
        for objects_item_data in self.objects:
            objects_item = objects_item_data.to_dict()
            objects.append(objects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domainControllerSettings": domain_controller_settings,
                "objects": objects,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ad_domain_model import ADDomainModel
        from ..models.ad_object_model import ADObjectModel

        d = dict(src_dict)
        domain_controller_settings = ADDomainModel.from_dict(d.pop("domainControllerSettings"))

        objects = []
        _objects = d.pop("objects")
        for objects_item_data in _objects:
            objects_item = ADObjectModel.from_dict(objects_item_data)

            objects.append(objects_item)

        active_directory_object_container_model = cls(
            domain_controller_settings=domain_controller_settings,
            objects=objects,
        )

        active_directory_object_container_model.additional_properties = d
        return active_directory_object_container_model

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
