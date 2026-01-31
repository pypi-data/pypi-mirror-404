from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_vi_host_type import EViHostType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel


T = TypeVar("T", bound="ViHostImportSpec")


@_attrs_define
class ViHostImportSpec:
    """Import settings for VMware vSphere server.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        vi_host_type (EViHostType): Type of the VMware vSphere server.
        credentials (CredentialsImportModel): Credentials used for connection.
        port (int | Unset): Port used to communicate with the server.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity.
    """

    name: str
    description: str
    type_: EManagedServerType
    vi_host_type: EViHostType
    credentials: CredentialsImportModel
    port: int | Unset = UNSET
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        vi_host_type = self.vi_host_type.value

        credentials = self.credentials.to_dict()

        port = self.port

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "viHostType": vi_host_type,
                "credentials": credentials,
            }
        )
        if port is not UNSET:
            field_dict["port"] = port
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        vi_host_type = EViHostType(d.pop("viHostType"))

        credentials = CredentialsImportModel.from_dict(d.pop("credentials"))

        port = d.pop("port", UNSET)

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        vi_host_import_spec = cls(
            name=name,
            description=description,
            type_=type_,
            vi_host_type=vi_host_type,
            credentials=credentials,
            port=port,
            certificate_thumbprint=certificate_thumbprint,
        )

        vi_host_import_spec.additional_properties = d
        return vi_host_import_spec

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
