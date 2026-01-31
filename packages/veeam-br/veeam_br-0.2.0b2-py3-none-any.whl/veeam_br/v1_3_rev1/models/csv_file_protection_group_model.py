from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_type import EProtectionGroupType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.csv_file_options_protection_group_model import CSVFileOptionsProtectionGroupModel
    from ..models.csv_file_protection_group_credential_model import CSVFileProtectionGroupCredentialModel
    from ..models.protection_group_options_model import ProtectionGroupOptionsModel


T = TypeVar("T", bound="CSVFileProtectionGroupModel")


@_attrs_define
class CSVFileProtectionGroupModel:
    """Protection group deployed from CSV file.

    Attributes:
        id (UUID): Protection group ID.
        name (str): Protection group name.
        description (str): Protection group description.
        type_ (EProtectionGroupType): Protection group type
        is_disabled (bool): If `true`, the protection group is disabled
        file (CSVFileOptionsProtectionGroupModel): CSV file settings.
        computer_names (list[str] | Unset): Array of computer names.
        credentials (CSVFileProtectionGroupCredentialModel | Unset): Authentication settings for protection group
            deployed with CSV file.
        options (ProtectionGroupOptionsModel | Unset): Protection group options.
    """

    id: UUID
    name: str
    description: str
    type_: EProtectionGroupType
    is_disabled: bool
    file: CSVFileOptionsProtectionGroupModel
    computer_names: list[str] | Unset = UNSET
    credentials: CSVFileProtectionGroupCredentialModel | Unset = UNSET
    options: ProtectionGroupOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        is_disabled = self.is_disabled

        file = self.file.to_dict()

        computer_names: list[str] | Unset = UNSET
        if not isinstance(self.computer_names, Unset):
            computer_names = self.computer_names

        credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.credentials, Unset):
            credentials = self.credentials.to_dict()

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "isDisabled": is_disabled,
                "file": file,
            }
        )
        if computer_names is not UNSET:
            field_dict["computerNames"] = computer_names
        if credentials is not UNSET:
            field_dict["credentials"] = credentials
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.csv_file_options_protection_group_model import CSVFileOptionsProtectionGroupModel
        from ..models.csv_file_protection_group_credential_model import CSVFileProtectionGroupCredentialModel
        from ..models.protection_group_options_model import ProtectionGroupOptionsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EProtectionGroupType(d.pop("type"))

        is_disabled = d.pop("isDisabled")

        file = CSVFileOptionsProtectionGroupModel.from_dict(d.pop("file"))

        computer_names = cast(list[str], d.pop("computerNames", UNSET))

        _credentials = d.pop("credentials", UNSET)
        credentials: CSVFileProtectionGroupCredentialModel | Unset
        if isinstance(_credentials, Unset):
            credentials = UNSET
        else:
            credentials = CSVFileProtectionGroupCredentialModel.from_dict(_credentials)

        _options = d.pop("options", UNSET)
        options: ProtectionGroupOptionsModel | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProtectionGroupOptionsModel.from_dict(_options)

        csv_file_protection_group_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            is_disabled=is_disabled,
            file=file,
            computer_names=computer_names,
            credentials=credentials,
            options=options,
        )

        csv_file_protection_group_model.additional_properties = d
        return csv_file_protection_group_model

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
