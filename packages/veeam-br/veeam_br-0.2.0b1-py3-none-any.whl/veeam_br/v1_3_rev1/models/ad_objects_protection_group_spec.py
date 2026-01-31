from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.active_directory_object_container_model import ActiveDirectoryObjectContainerModel
    from ..models.ad_objects_protection_group_credential_model import ADObjectsProtectionGroupCredentialModel
    from ..models.ad_objects_protection_group_exclusions_model import ADObjectsProtectionGroupExclusionsModel
    from ..models.protection_group_options_model import ProtectionGroupOptionsModel


T = TypeVar("T", bound="ADObjectsProtectionGroupSpec")


@_attrs_define
class ADObjectsProtectionGroupSpec:
    """Protection group for Active Directory objects.

    Attributes:
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        active_directory (ActiveDirectoryObjectContainerModel): Active Directory container.
        credentials (ADObjectsProtectionGroupCredentialModel): Authentication settings for Active Directory objects.
        tag (str | Unset): Protection group tag.
        exclusions (ADObjectsProtectionGroupExclusionsModel | Unset): Exclusion settings for Active Directory objects.
        options (ProtectionGroupOptionsModel | Unset): Protection group options.
    """

    name: str
    description: str
    type_: EProtectionGroupType
    active_directory: ActiveDirectoryObjectContainerModel
    credentials: ADObjectsProtectionGroupCredentialModel
    tag: str | Unset = UNSET
    exclusions: ADObjectsProtectionGroupExclusionsModel | Unset = UNSET
    options: ProtectionGroupOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        active_directory = self.active_directory.to_dict()

        credentials = self.credentials.to_dict()

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
                "activeDirectory": active_directory,
                "credentials": credentials,
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
        from ..models.active_directory_object_container_model import ActiveDirectoryObjectContainerModel
        from ..models.ad_objects_protection_group_credential_model import ADObjectsProtectionGroupCredentialModel
        from ..models.ad_objects_protection_group_exclusions_model import ADObjectsProtectionGroupExclusionsModel
        from ..models.protection_group_options_model import ProtectionGroupOptionsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        active_directory = ActiveDirectoryObjectContainerModel.from_dict(d.pop("activeDirectory"))

        credentials = ADObjectsProtectionGroupCredentialModel.from_dict(d.pop("credentials"))

        tag = d.pop("tag", UNSET)

        _exclusions = d.pop("exclusions", UNSET)
        exclusions: ADObjectsProtectionGroupExclusionsModel | Unset
        if isinstance(_exclusions, Unset):
            exclusions = UNSET
        else:
            exclusions = ADObjectsProtectionGroupExclusionsModel.from_dict(_exclusions)

        _options = d.pop("options", UNSET)
        options: ProtectionGroupOptionsModel | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProtectionGroupOptionsModel.from_dict(_options)

        ad_objects_protection_group_spec = cls(
            name=name,
            description=description,
            type_=type_,
            active_directory=active_directory,
            credentials=credentials,
            tag=tag,
            exclusions=exclusions,
            options=options,
        )

        ad_objects_protection_group_spec.additional_properties = d
        return ad_objects_protection_group_spec

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
