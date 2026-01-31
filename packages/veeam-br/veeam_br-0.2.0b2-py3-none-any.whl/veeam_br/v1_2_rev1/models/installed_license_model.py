from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_installed_license_cloud_connect_mode import EInstalledLicenseCloudConnectMode
from ..models.e_installed_license_edition import EInstalledLicenseEdition
from ..models.e_installed_license_status import EInstalledLicenseStatus
from ..models.e_installed_license_type import EInstalledLicenseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.capacity_license_summary_model import CapacityLicenseSummaryModel
    from ..models.instance_license_summary_model import InstanceLicenseSummaryModel
    from ..models.socket_license_summary_model import SocketLicenseSummaryModel


T = TypeVar("T", bound="InstalledLicenseModel")


@_attrs_define
class InstalledLicenseModel:
    """Details on the installed license.

    Attributes:
        status (EInstalledLicenseStatus): License status.
        type_ (EInstalledLicenseType): License type.
        edition (EInstalledLicenseEdition): License edition.
        licensed_to (str): Person or organization to which the license was issued.
        support_id (str): Support ID required for contacting Veeam Support.
        auto_update_enabled (bool): If `true`, the license is automatically updated.
        free_agent_instance_consumption_enabled (bool): If `true`, unlicensed Veeam Agents consume instances.
        cloud_connect (EInstalledLicenseCloudConnectMode): Cloud Connect license mode.
        expiration_date (datetime.datetime | Unset): Expiration date and time of the license.
        socket_license_summary (SocketLicenseSummaryModel | Unset): Details on per-socket license usage.
        instance_license_summary (InstanceLicenseSummaryModel | Unset): Details on per-instance license consumption.
        capacity_license_summary (CapacityLicenseSummaryModel | Unset): Details on total and consumed capacity by
            workload.
        support_expiration_date (datetime.datetime | Unset): Expiration date and time for the support contract.
    """

    status: EInstalledLicenseStatus
    type_: EInstalledLicenseType
    edition: EInstalledLicenseEdition
    licensed_to: str
    support_id: str
    auto_update_enabled: bool
    free_agent_instance_consumption_enabled: bool
    cloud_connect: EInstalledLicenseCloudConnectMode
    expiration_date: datetime.datetime | Unset = UNSET
    socket_license_summary: SocketLicenseSummaryModel | Unset = UNSET
    instance_license_summary: InstanceLicenseSummaryModel | Unset = UNSET
    capacity_license_summary: CapacityLicenseSummaryModel | Unset = UNSET
    support_expiration_date: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        type_ = self.type_.value

        edition = self.edition.value

        licensed_to = self.licensed_to

        support_id = self.support_id

        auto_update_enabled = self.auto_update_enabled

        free_agent_instance_consumption_enabled = self.free_agent_instance_consumption_enabled

        cloud_connect = self.cloud_connect.value

        expiration_date: str | Unset = UNSET
        if not isinstance(self.expiration_date, Unset):
            expiration_date = self.expiration_date.isoformat()

        socket_license_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.socket_license_summary, Unset):
            socket_license_summary = self.socket_license_summary.to_dict()

        instance_license_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.instance_license_summary, Unset):
            instance_license_summary = self.instance_license_summary.to_dict()

        capacity_license_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.capacity_license_summary, Unset):
            capacity_license_summary = self.capacity_license_summary.to_dict()

        support_expiration_date: str | Unset = UNSET
        if not isinstance(self.support_expiration_date, Unset):
            support_expiration_date = self.support_expiration_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "type": type_,
                "edition": edition,
                "licensedTo": licensed_to,
                "supportId": support_id,
                "autoUpdateEnabled": auto_update_enabled,
                "freeAgentInstanceConsumptionEnabled": free_agent_instance_consumption_enabled,
                "cloudConnect": cloud_connect,
            }
        )
        if expiration_date is not UNSET:
            field_dict["expirationDate"] = expiration_date
        if socket_license_summary is not UNSET:
            field_dict["socketLicenseSummary"] = socket_license_summary
        if instance_license_summary is not UNSET:
            field_dict["instanceLicenseSummary"] = instance_license_summary
        if capacity_license_summary is not UNSET:
            field_dict["capacityLicenseSummary"] = capacity_license_summary
        if support_expiration_date is not UNSET:
            field_dict["supportExpirationDate"] = support_expiration_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.capacity_license_summary_model import CapacityLicenseSummaryModel
        from ..models.instance_license_summary_model import InstanceLicenseSummaryModel
        from ..models.socket_license_summary_model import SocketLicenseSummaryModel

        d = dict(src_dict)
        status = EInstalledLicenseStatus(d.pop("status"))

        type_ = EInstalledLicenseType(d.pop("type"))

        edition = EInstalledLicenseEdition(d.pop("edition"))

        licensed_to = d.pop("licensedTo")

        support_id = d.pop("supportId")

        auto_update_enabled = d.pop("autoUpdateEnabled")

        free_agent_instance_consumption_enabled = d.pop("freeAgentInstanceConsumptionEnabled")

        cloud_connect = EInstalledLicenseCloudConnectMode(d.pop("cloudConnect"))

        _expiration_date = d.pop("expirationDate", UNSET)
        expiration_date: datetime.datetime | Unset
        if isinstance(_expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = isoparse(_expiration_date)

        _socket_license_summary = d.pop("socketLicenseSummary", UNSET)
        socket_license_summary: SocketLicenseSummaryModel | Unset
        if isinstance(_socket_license_summary, Unset):
            socket_license_summary = UNSET
        else:
            socket_license_summary = SocketLicenseSummaryModel.from_dict(_socket_license_summary)

        _instance_license_summary = d.pop("instanceLicenseSummary", UNSET)
        instance_license_summary: InstanceLicenseSummaryModel | Unset
        if isinstance(_instance_license_summary, Unset):
            instance_license_summary = UNSET
        else:
            instance_license_summary = InstanceLicenseSummaryModel.from_dict(_instance_license_summary)

        _capacity_license_summary = d.pop("capacityLicenseSummary", UNSET)
        capacity_license_summary: CapacityLicenseSummaryModel | Unset
        if isinstance(_capacity_license_summary, Unset):
            capacity_license_summary = UNSET
        else:
            capacity_license_summary = CapacityLicenseSummaryModel.from_dict(_capacity_license_summary)

        _support_expiration_date = d.pop("supportExpirationDate", UNSET)
        support_expiration_date: datetime.datetime | Unset
        if isinstance(_support_expiration_date, Unset):
            support_expiration_date = UNSET
        else:
            support_expiration_date = isoparse(_support_expiration_date)

        installed_license_model = cls(
            status=status,
            type_=type_,
            edition=edition,
            licensed_to=licensed_to,
            support_id=support_id,
            auto_update_enabled=auto_update_enabled,
            free_agent_instance_consumption_enabled=free_agent_instance_consumption_enabled,
            cloud_connect=cloud_connect,
            expiration_date=expiration_date,
            socket_license_summary=socket_license_summary,
            instance_license_summary=instance_license_summary,
            capacity_license_summary=capacity_license_summary,
            support_expiration_date=support_expiration_date,
        )

        installed_license_model.additional_properties = d
        return installed_license_model

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
