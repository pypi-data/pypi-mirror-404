from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.repository_share_gateway_import_spec import RepositoryShareGatewayImportSpec


T = TypeVar("T", bound="SmbRepositoryShareSettingsSpec")


@_attrs_define
class SmbRepositoryShareSettingsSpec:
    """SMB share settings.

    Attributes:
        share_path (str): Path to the shared folder that is used as a backup repository.
        credentials (CredentialsImportModel): Credentials used for connection.
        gateway_server (RepositoryShareGatewayImportSpec | Unset): Import settings for the gateway server.
    """

    share_path: str
    credentials: CredentialsImportModel
    gateway_server: RepositoryShareGatewayImportSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        share_path = self.share_path

        credentials = self.credentials.to_dict()

        gateway_server: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gateway_server, Unset):
            gateway_server = self.gateway_server.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sharePath": share_path,
                "credentials": credentials,
            }
        )
        if gateway_server is not UNSET:
            field_dict["gatewayServer"] = gateway_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.repository_share_gateway_import_spec import RepositoryShareGatewayImportSpec

        d = dict(src_dict)
        share_path = d.pop("sharePath")

        credentials = CredentialsImportModel.from_dict(d.pop("credentials"))

        _gateway_server = d.pop("gatewayServer", UNSET)
        gateway_server: RepositoryShareGatewayImportSpec | Unset
        if isinstance(_gateway_server, Unset):
            gateway_server = UNSET
        else:
            gateway_server = RepositoryShareGatewayImportSpec.from_dict(_gateway_server)

        smb_repository_share_settings_spec = cls(
            share_path=share_path,
            credentials=credentials,
            gateway_server=gateway_server,
        )

        smb_repository_share_settings_spec.additional_properties = d
        return smb_repository_share_settings_spec

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
