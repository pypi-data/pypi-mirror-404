from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.evbr_server_platform import EVBRServerPlatform

if TYPE_CHECKING:
    from ..models.veeam_registration_info import VeeamRegistrationInfo


T = TypeVar("T", bound="ServerInfoModel")


@_attrs_define
class ServerInfoModel:
    """Backup server information.

    Attributes:
        vbr_id (str): Veeam Backup & Replication installation ID.
        name (str): Full DNS name or IP address of the backup server.
        build_version (str): Veeam Backup & Replication build number.
        patches (list[str]): Array of Veeam Backup & Replication cumulative patches installed on the backup server.
        database_vendor (str): Database engine (Microsoft SQL Server or PostgreSQL).
        sql_server_edition (str): Database server edition.
        sql_server_version (str): Database server version.
        database_schema_version (str): Database schema version.
        database_content_version (str): Database content version.
        veeam_registration (VeeamRegistrationInfo): Details on registering a backup server on the My Account portal.
        platform (EVBRServerPlatform): Backup server platform.
    """

    vbr_id: str
    name: str
    build_version: str
    patches: list[str]
    database_vendor: str
    sql_server_edition: str
    sql_server_version: str
    database_schema_version: str
    database_content_version: str
    veeam_registration: VeeamRegistrationInfo
    platform: EVBRServerPlatform
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vbr_id = self.vbr_id

        name = self.name

        build_version = self.build_version

        patches = self.patches

        database_vendor = self.database_vendor

        sql_server_edition = self.sql_server_edition

        sql_server_version = self.sql_server_version

        database_schema_version = self.database_schema_version

        database_content_version = self.database_content_version

        veeam_registration = self.veeam_registration.to_dict()

        platform = self.platform.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vbrId": vbr_id,
                "name": name,
                "buildVersion": build_version,
                "patches": patches,
                "databaseVendor": database_vendor,
                "sqlServerEdition": sql_server_edition,
                "sqlServerVersion": sql_server_version,
                "databaseSchemaVersion": database_schema_version,
                "databaseContentVersion": database_content_version,
                "veeamRegistration": veeam_registration,
                "platform": platform,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.veeam_registration_info import VeeamRegistrationInfo

        d = dict(src_dict)
        vbr_id = d.pop("vbrId")

        name = d.pop("name")

        build_version = d.pop("buildVersion")

        patches = cast(list[str], d.pop("patches"))

        database_vendor = d.pop("databaseVendor")

        sql_server_edition = d.pop("sqlServerEdition")

        sql_server_version = d.pop("sqlServerVersion")

        database_schema_version = d.pop("databaseSchemaVersion")

        database_content_version = d.pop("databaseContentVersion")

        veeam_registration = VeeamRegistrationInfo.from_dict(d.pop("veeamRegistration"))

        platform = EVBRServerPlatform(d.pop("platform"))

        server_info_model = cls(
            vbr_id=vbr_id,
            name=name,
            build_version=build_version,
            patches=patches,
            database_vendor=database_vendor,
            sql_server_edition=sql_server_edition,
            sql_server_version=sql_server_version,
            database_schema_version=database_schema_version,
            database_content_version=database_content_version,
            veeam_registration=veeam_registration,
            platform=platform,
        )

        server_info_model.additional_properties = d
        return server_info_model

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
