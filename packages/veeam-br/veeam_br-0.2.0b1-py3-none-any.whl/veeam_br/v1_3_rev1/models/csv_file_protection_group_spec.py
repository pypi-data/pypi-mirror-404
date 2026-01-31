from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.csv_file_options_protection_group_model import CSVFileOptionsProtectionGroupModel
    from ..models.csv_file_protection_group_credential_model import CSVFileProtectionGroupCredentialModel
    from ..models.protection_group_options_model import ProtectionGroupOptionsModel


T = TypeVar("T", bound="CSVFileProtectionGroupSpec")


@_attrs_define
class CSVFileProtectionGroupSpec:
    """Protection group deployed from CSV file.

    Attributes:
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        file (CSVFileOptionsProtectionGroupModel): CSV file settings.
        credentials (CSVFileProtectionGroupCredentialModel): Authentication settings for protection group deployed with
            CSV file.
        tag (str | Unset): Protection group tag.
        options (ProtectionGroupOptionsModel | Unset): Protection group options.
    """

    name: str
    description: str
    type_: EProtectionGroupType
    file: CSVFileOptionsProtectionGroupModel
    credentials: CSVFileProtectionGroupCredentialModel
    tag: str | Unset = UNSET
    options: ProtectionGroupOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        file = self.file.to_dict()

        credentials = self.credentials.to_dict()

        tag = self.tag

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
                "file": file,
                "credentials": credentials,
            }
        )
        if tag is not UNSET:
            field_dict["tag"] = tag
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.csv_file_options_protection_group_model import CSVFileOptionsProtectionGroupModel
        from ..models.csv_file_protection_group_credential_model import CSVFileProtectionGroupCredentialModel
        from ..models.protection_group_options_model import ProtectionGroupOptionsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        file = CSVFileOptionsProtectionGroupModel.from_dict(d.pop("file"))

        credentials = CSVFileProtectionGroupCredentialModel.from_dict(d.pop("credentials"))

        tag = d.pop("tag", UNSET)

        _options = d.pop("options", UNSET)
        options: ProtectionGroupOptionsModel | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProtectionGroupOptionsModel.from_dict(_options)

        csv_file_protection_group_spec = cls(
            name=name,
            description=description,
            type_=type_,
            file=file,
            credentials=credentials,
            tag=tag,
            options=options,
        )

        csv_file_protection_group_spec.additional_properties = d
        return csv_file_protection_group_spec

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
