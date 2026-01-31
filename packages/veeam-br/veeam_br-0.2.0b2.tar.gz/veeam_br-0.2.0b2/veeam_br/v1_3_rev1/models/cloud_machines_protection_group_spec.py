from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_machines_protection_group_account_model import CloudMachinesProtectionGroupAccountModel
    from ..models.cloud_machines_protection_group_exclusions_model import CloudMachinesProtectionGroupExclusionsModel
    from ..models.cloud_machines_protection_group_objects_model import CloudMachinesProtectionGroupObjectsModel
    from ..models.protection_group_options_model import ProtectionGroupOptionsModel


T = TypeVar("T", bound="CloudMachinesProtectionGroupSpec")


@_attrs_define
class CloudMachinesProtectionGroupSpec:
    """Protection group for cloud machines.

    Attributes:
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        cloud_account (CloudMachinesProtectionGroupAccountModel): Account settings for cloud objects.
        cloud_machines (list[CloudMachinesProtectionGroupObjectsModel]): Array of cloud objects.
        tag (str | Unset): Protection group tag.
        exclusions (CloudMachinesProtectionGroupExclusionsModel | Unset): Exclusion settings for cloud objects.
        options (ProtectionGroupOptionsModel | Unset): Protection group options.
    """

    name: str
    description: str
    type_: EProtectionGroupType
    cloud_account: CloudMachinesProtectionGroupAccountModel
    cloud_machines: list[CloudMachinesProtectionGroupObjectsModel]
    tag: str | Unset = UNSET
    exclusions: CloudMachinesProtectionGroupExclusionsModel | Unset = UNSET
    options: ProtectionGroupOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        cloud_account = self.cloud_account.to_dict()

        cloud_machines = []
        for cloud_machines_item_data in self.cloud_machines:
            cloud_machines_item = cloud_machines_item_data.to_dict()
            cloud_machines.append(cloud_machines_item)

        tag = self.tag

        exclusions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.exclusions, Unset):
            exclusions = self.exclusions.to_dict()

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "cloudAccount": cloud_account,
                "cloudMachines": cloud_machines,
            }
        )
        if tag is not UNSET:
            field_dict["tag"] = tag
        if exclusions is not UNSET:
            field_dict["exclusions"] = exclusions
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_machines_protection_group_account_model import CloudMachinesProtectionGroupAccountModel
        from ..models.cloud_machines_protection_group_exclusions_model import (
            CloudMachinesProtectionGroupExclusionsModel,
        )
        from ..models.cloud_machines_protection_group_objects_model import CloudMachinesProtectionGroupObjectsModel
        from ..models.protection_group_options_model import ProtectionGroupOptionsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        cloud_account = CloudMachinesProtectionGroupAccountModel.from_dict(d.pop("cloudAccount"))

        cloud_machines = []
        _cloud_machines = d.pop("cloudMachines")
        for cloud_machines_item_data in _cloud_machines:
            cloud_machines_item = CloudMachinesProtectionGroupObjectsModel.from_dict(cloud_machines_item_data)

            cloud_machines.append(cloud_machines_item)

        tag = d.pop("tag", UNSET)

        _exclusions = d.pop("exclusions", UNSET)
        exclusions: CloudMachinesProtectionGroupExclusionsModel | Unset
        if isinstance(_exclusions, Unset):
            exclusions = UNSET
        else:
            exclusions = CloudMachinesProtectionGroupExclusionsModel.from_dict(_exclusions)

        _options = d.pop("options", UNSET)
        options: ProtectionGroupOptionsModel | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProtectionGroupOptionsModel.from_dict(_options)

        cloud_machines_protection_group_spec = cls(
            name=name,
            description=description,
            type_=type_,
            cloud_account=cloud_account,
            cloud_machines=cloud_machines,
            tag=tag,
            exclusions=exclusions,
            options=options,
        )

        cloud_machines_protection_group_spec.additional_properties = d
        return cloud_machines_protection_group_spec

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
