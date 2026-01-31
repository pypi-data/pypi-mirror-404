from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.repository_share_gateway_model import RepositoryShareGatewayModel


T = TypeVar("T", bound="NfsRepositoryShareSettingsModel")


@_attrs_define
class NfsRepositoryShareSettingsModel:
    """NFS share settings.

    Attributes:
        share_path (str): Path to the shared folder that is used as a backup repository.
        gateway_server (RepositoryShareGatewayModel | Unset): Settings for the gateway server.
    """

    share_path: str
    gateway_server: RepositoryShareGatewayModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        share_path = self.share_path

        gateway_server: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gateway_server, Unset):
            gateway_server = self.gateway_server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sharePath": share_path,
            }
        )
        if gateway_server is not UNSET:
            field_dict["gatewayServer"] = gateway_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.repository_share_gateway_model import RepositoryShareGatewayModel

        d = dict(src_dict)
        share_path = d.pop("sharePath")

        _gateway_server = d.pop("gatewayServer", UNSET)
        gateway_server: RepositoryShareGatewayModel | Unset
        if isinstance(_gateway_server, Unset):
            gateway_server = UNSET
        else:
            gateway_server = RepositoryShareGatewayModel.from_dict(_gateway_server)

        nfs_repository_share_settings_model = cls(
            share_path=share_path,
            gateway_server=gateway_server,
        )

        nfs_repository_share_settings_model.additional_properties = d
        return nfs_repository_share_settings_model

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
