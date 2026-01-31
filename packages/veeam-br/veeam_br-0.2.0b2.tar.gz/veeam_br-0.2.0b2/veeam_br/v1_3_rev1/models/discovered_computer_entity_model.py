from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_agent_status import EAgentStatus
from ..models.e_discovered_computer_state import EDiscoveredComputerState
from ..models.e_discovered_entity_type import EDiscoveredEntityType
from ..models.e_driver_status import EDriverStatus
from ..models.e_operating_system import EOperatingSystem
from ..models.e_operating_system_platform import EOperatingSystemPlatform
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.discovered_computer_plugin_model import DiscoveredComputerPluginModel


T = TypeVar("T", bound="DiscoveredComputerEntityModel")


@_attrs_define
class DiscoveredComputerEntityModel:
    """Discovered computer settings.

    Attributes:
        id (UUID): Discovered entity ID.
        name (str): Discovered entity name.
        parent_id (UUID): Parent ID of the discovered entity.
        protection_group_id (UUID): Protection group ID.
        state (EDiscoveredComputerState): State of the discovered computer.
        agent_status (EAgentStatus): Status of the Veeam Agent on a discovered computer.
        driver_status (EDriverStatus): Status of the driver on a discovered computer.
        ip_addresses (list[str]): Array of IP addresses of the discovered computer.
        object_id (UUID): Object ID.
        plugins (list[DiscoveredComputerPluginModel]): Array of installed plug-ins.
        is_trusted (bool): If `true`, the discovered computer is trusted and the certificate thumbprint is up to date.
        type_ (EDiscoveredEntityType | Unset): Discovered entity type.
        agent_version (str | Unset): Version of the backup agent installed on the discovered computer.
        driver_version (str | Unset): Version of the driver installed on the discovered computer.
        reboot_required (bool | Unset): If `true`, the discovered computer must be rebooted.
        last_connected (datetime.datetime | Unset): Date and time of the last connection with Veeam Agent installed on
            the discovered computer.
        operating_system (EOperatingSystem | Unset): Operating system.
        operating_system_platform (EOperatingSystemPlatform | Unset): Operating system platform.
        operating_system_version (str | Unset): Operating system version of the discovered computer.
        operating_system_update_version (int | Unset): Update version of the operating system of the discovered
            computer.
        bios_uuid (UUID | Unset): BIOS UUID.
    """

    id: UUID
    name: str
    parent_id: UUID
    protection_group_id: UUID
    state: EDiscoveredComputerState
    agent_status: EAgentStatus
    driver_status: EDriverStatus
    ip_addresses: list[str]
    object_id: UUID
    plugins: list[DiscoveredComputerPluginModel]
    is_trusted: bool
    type_: EDiscoveredEntityType | Unset = UNSET
    agent_version: str | Unset = UNSET
    driver_version: str | Unset = UNSET
    reboot_required: bool | Unset = UNSET
    last_connected: datetime.datetime | Unset = UNSET
    operating_system: EOperatingSystem | Unset = UNSET
    operating_system_platform: EOperatingSystemPlatform | Unset = UNSET
    operating_system_version: str | Unset = UNSET
    operating_system_update_version: int | Unset = UNSET
    bios_uuid: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        parent_id = str(self.parent_id)

        protection_group_id = str(self.protection_group_id)

        state = self.state.value

        agent_status = self.agent_status.value

        driver_status = self.driver_status.value

        ip_addresses = self.ip_addresses

        object_id = str(self.object_id)

        plugins = []
        for plugins_item_data in self.plugins:
            plugins_item = plugins_item_data.to_dict()
            plugins.append(plugins_item)

        is_trusted = self.is_trusted

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        agent_version = self.agent_version

        driver_version = self.driver_version

        reboot_required = self.reboot_required

        last_connected: str | Unset = UNSET
        if not isinstance(self.last_connected, Unset):
            last_connected = self.last_connected.isoformat()

        operating_system: str | Unset = UNSET
        if not isinstance(self.operating_system, Unset):
            operating_system = self.operating_system.value

        operating_system_platform: str | Unset = UNSET
        if not isinstance(self.operating_system_platform, Unset):
            operating_system_platform = self.operating_system_platform.value

        operating_system_version = self.operating_system_version

        operating_system_update_version = self.operating_system_update_version

        bios_uuid: str | Unset = UNSET
        if not isinstance(self.bios_uuid, Unset):
            bios_uuid = str(self.bios_uuid)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "parentId": parent_id,
                "protectionGroupId": protection_group_id,
                "state": state,
                "agentStatus": agent_status,
                "driverStatus": driver_status,
                "ipAddresses": ip_addresses,
                "objectId": object_id,
                "plugins": plugins,
                "isTrusted": is_trusted,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if agent_version is not UNSET:
            field_dict["agentVersion"] = agent_version
        if driver_version is not UNSET:
            field_dict["driverVersion"] = driver_version
        if reboot_required is not UNSET:
            field_dict["rebootRequired"] = reboot_required
        if last_connected is not UNSET:
            field_dict["lastConnected"] = last_connected
        if operating_system is not UNSET:
            field_dict["operatingSystem"] = operating_system
        if operating_system_platform is not UNSET:
            field_dict["operatingSystemPlatform"] = operating_system_platform
        if operating_system_version is not UNSET:
            field_dict["operatingSystemVersion"] = operating_system_version
        if operating_system_update_version is not UNSET:
            field_dict["operatingSystemUpdateVersion"] = operating_system_update_version
        if bios_uuid is not UNSET:
            field_dict["biosUuid"] = bios_uuid

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.discovered_computer_plugin_model import DiscoveredComputerPluginModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        parent_id = UUID(d.pop("parentId"))

        protection_group_id = UUID(d.pop("protectionGroupId"))

        state = EDiscoveredComputerState(d.pop("state"))

        agent_status = EAgentStatus(d.pop("agentStatus"))

        driver_status = EDriverStatus(d.pop("driverStatus"))

        ip_addresses = cast(list[str], d.pop("ipAddresses"))

        object_id = UUID(d.pop("objectId"))

        plugins = []
        _plugins = d.pop("plugins")
        for plugins_item_data in _plugins:
            plugins_item = DiscoveredComputerPluginModel.from_dict(plugins_item_data)

            plugins.append(plugins_item)

        is_trusted = d.pop("isTrusted")

        _type_ = d.pop("type", UNSET)
        type_: EDiscoveredEntityType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EDiscoveredEntityType(_type_)

        agent_version = d.pop("agentVersion", UNSET)

        driver_version = d.pop("driverVersion", UNSET)

        reboot_required = d.pop("rebootRequired", UNSET)

        _last_connected = d.pop("lastConnected", UNSET)
        last_connected: datetime.datetime | Unset
        if isinstance(_last_connected, Unset):
            last_connected = UNSET
        else:
            last_connected = isoparse(_last_connected)

        _operating_system = d.pop("operatingSystem", UNSET)
        operating_system: EOperatingSystem | Unset
        if isinstance(_operating_system, Unset):
            operating_system = UNSET
        else:
            operating_system = EOperatingSystem(_operating_system)

        _operating_system_platform = d.pop("operatingSystemPlatform", UNSET)
        operating_system_platform: EOperatingSystemPlatform | Unset
        if isinstance(_operating_system_platform, Unset):
            operating_system_platform = UNSET
        else:
            operating_system_platform = EOperatingSystemPlatform(_operating_system_platform)

        operating_system_version = d.pop("operatingSystemVersion", UNSET)

        operating_system_update_version = d.pop("operatingSystemUpdateVersion", UNSET)

        _bios_uuid = d.pop("biosUuid", UNSET)
        bios_uuid: UUID | Unset
        if isinstance(_bios_uuid, Unset):
            bios_uuid = UNSET
        else:
            bios_uuid = UUID(_bios_uuid)

        discovered_computer_entity_model = cls(
            id=id,
            name=name,
            parent_id=parent_id,
            protection_group_id=protection_group_id,
            state=state,
            agent_status=agent_status,
            driver_status=driver_status,
            ip_addresses=ip_addresses,
            object_id=object_id,
            plugins=plugins,
            is_trusted=is_trusted,
            type_=type_,
            agent_version=agent_version,
            driver_version=driver_version,
            reboot_required=reboot_required,
            last_connected=last_connected,
            operating_system=operating_system,
            operating_system_platform=operating_system_platform,
            operating_system_version=operating_system_version,
            operating_system_update_version=operating_system_update_version,
            bios_uuid=bios_uuid,
        )

        discovered_computer_entity_model.additional_properties = d
        return discovered_computer_entity_model

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
