from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_mount_server_type import EMountServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_server_options_model import MountServerOptionsModel


T = TypeVar("T", bound="MountServerModel")


@_attrs_define
class MountServerModel:
    """Mount server.

    Attributes:
        id (UUID): Mount server ID. The ID is the same as the ID of the managed server that was assigned a mount server
            role.
        type_ (EMountServerType | Unset): Mount server type.
        settings (MountServerOptionsModel | Unset): Mount server settings.
        is_default (bool | Unset): If `true`, the mount server is set as default.
    """

    id: UUID
    type_: EMountServerType | Unset = UNSET
    settings: MountServerOptionsModel | Unset = UNSET
    is_default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if settings is not UNSET:
            field_dict["settings"] = settings
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_server_options_model import MountServerOptionsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        _type_ = d.pop("type", UNSET)
        type_: EMountServerType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EMountServerType(_type_)

        _settings = d.pop("settings", UNSET)
        settings: MountServerOptionsModel | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = MountServerOptionsModel.from_dict(_settings)

        is_default = d.pop("isDefault", UNSET)

        mount_server_model = cls(
            id=id,
            type_=type_,
            settings=settings,
            is_default=is_default,
        )

        mount_server_model.additional_properties = d
        return mount_server_model

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
