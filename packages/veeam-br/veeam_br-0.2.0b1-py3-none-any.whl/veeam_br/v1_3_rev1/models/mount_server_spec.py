from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_server_options_model import MountServerOptionsModel


T = TypeVar("T", bound="MountServerSpec")


@_attrs_define
class MountServerSpec:
    """Mount server.

    Attributes:
        host_id (UUID): Host ID. To get the ID, run the [Get All Servers](Managed-
            Servers#operation/GetAllManagedServers) request.
        settings (MountServerOptionsModel | Unset): Mount server settings.
        set_as_default (bool | Unset): If `true`, the mount server will be set as the default mount server.
    """

    host_id: UUID
    settings: MountServerOptionsModel | Unset = UNSET
    set_as_default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_id = str(self.host_id)

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        set_as_default = self.set_as_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostId": host_id,
            }
        )
        if settings is not UNSET:
            field_dict["settings"] = settings
        if set_as_default is not UNSET:
            field_dict["setAsDefault"] = set_as_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mount_server_options_model import MountServerOptionsModel

        d = dict(src_dict)
        host_id = UUID(d.pop("hostId"))

        _settings = d.pop("settings", UNSET)
        settings: MountServerOptionsModel | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = MountServerOptionsModel.from_dict(_settings)

        set_as_default = d.pop("setAsDefault", UNSET)

        mount_server_spec = cls(
            host_id=host_id,
            settings=settings,
            set_as_default=set_as_default,
        )

        mount_server_spec.additional_properties = d
        return mount_server_spec

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
