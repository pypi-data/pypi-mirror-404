from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.replica_job_guest_processing_model import ReplicaJobGuestProcessingModel
    from ..models.replica_job_re_ip_rules_model import ReplicaJobReIpRulesModel
    from ..models.v_sphere_replica_job_data_transfer_model import VSphereReplicaJobDataTransferModel
    from ..models.v_sphere_replica_job_destination_model import VSphereReplicaJobDestinationModel
    from ..models.v_sphere_replica_job_network_mapping_model import VSphereReplicaJobNetworkMappingModel
    from ..models.v_sphere_replica_job_settings_model import VSphereReplicaJobSettingsModel
    from ..models.v_sphere_replica_job_virtual_machines_spec import VSphereReplicaJobVirtualMachinesSpec
    from ..models.v_sphere_replica_seeding_model import VSphereReplicaSeedingModel


T = TypeVar("T", bound="VSphereReplicaJobSpec")


@_attrs_define
class VSphereReplicaJobSpec:
    """
    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        virtual_machines (VSphereReplicaJobVirtualMachinesSpec): Included and excluded objects.
        destination (VSphereReplicaJobDestinationModel): Replica destination&#58; target host or cluster, target
            resource pool, target folder, target datastore and mapping rules.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job higher than other
            similar jobs and allocates resources to it in the first place.
        network (list[VSphereReplicaJobNetworkMappingModel] | Unset): Array of mapping rules for networks. Use mapping
            rules if destination site networks do not match your production site networks.
        re_ip (ReplicaJobReIpRulesModel | Unset): Re-IP rules that map IPs in the production site to IPs in the disaster
            recovery site.
        job_settings (VSphereReplicaJobSettingsModel | Unset): Replication job settings.
        data_transfer (VSphereReplicaJobDataTransferModel | Unset): Data transfer settings.
        seeding (VSphereReplicaSeedingModel | Unset): Replica seeding and mapping settings.
        guest_processing (ReplicaJobGuestProcessingModel | Unset): Guest processing settings.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    name: str
    type_: EJobType
    description: str
    virtual_machines: VSphereReplicaJobVirtualMachinesSpec
    destination: VSphereReplicaJobDestinationModel
    is_high_priority: bool | Unset = UNSET
    network: list[VSphereReplicaJobNetworkMappingModel] | Unset = UNSET
    re_ip: ReplicaJobReIpRulesModel | Unset = UNSET
    job_settings: VSphereReplicaJobSettingsModel | Unset = UNSET
    data_transfer: VSphereReplicaJobDataTransferModel | Unset = UNSET
    seeding: VSphereReplicaSeedingModel | Unset = UNSET
    guest_processing: ReplicaJobGuestProcessingModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        description = self.description

        virtual_machines = self.virtual_machines.to_dict()

        destination = self.destination.to_dict()

        is_high_priority = self.is_high_priority

        network: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.network, Unset):
            network = []
            for network_item_data in self.network:
                network_item = network_item_data.to_dict()
                network.append(network_item)

        re_ip: dict[str, Any] | Unset = UNSET
        if not isinstance(self.re_ip, Unset):
            re_ip = self.re_ip.to_dict()

        job_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.job_settings, Unset):
            job_settings = self.job_settings.to_dict()

        data_transfer: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data_transfer, Unset):
            data_transfer = self.data_transfer.to_dict()

        seeding: dict[str, Any] | Unset = UNSET
        if not isinstance(self.seeding, Unset):
            seeding = self.seeding.to_dict()

        guest_processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.guest_processing, Unset):
            guest_processing = self.guest_processing.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "description": description,
                "virtualMachines": virtual_machines,
                "destination": destination,
            }
        )
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if network is not UNSET:
            field_dict["network"] = network
        if re_ip is not UNSET:
            field_dict["reIp"] = re_ip
        if job_settings is not UNSET:
            field_dict["jobSettings"] = job_settings
        if data_transfer is not UNSET:
            field_dict["dataTransfer"] = data_transfer
        if seeding is not UNSET:
            field_dict["seeding"] = seeding
        if guest_processing is not UNSET:
            field_dict["guestProcessing"] = guest_processing
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.replica_job_guest_processing_model import ReplicaJobGuestProcessingModel
        from ..models.replica_job_re_ip_rules_model import ReplicaJobReIpRulesModel
        from ..models.v_sphere_replica_job_data_transfer_model import VSphereReplicaJobDataTransferModel
        from ..models.v_sphere_replica_job_destination_model import VSphereReplicaJobDestinationModel
        from ..models.v_sphere_replica_job_network_mapping_model import VSphereReplicaJobNetworkMappingModel
        from ..models.v_sphere_replica_job_settings_model import VSphereReplicaJobSettingsModel
        from ..models.v_sphere_replica_job_virtual_machines_spec import VSphereReplicaJobVirtualMachinesSpec
        from ..models.v_sphere_replica_seeding_model import VSphereReplicaSeedingModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        virtual_machines = VSphereReplicaJobVirtualMachinesSpec.from_dict(d.pop("virtualMachines"))

        destination = VSphereReplicaJobDestinationModel.from_dict(d.pop("destination"))

        is_high_priority = d.pop("isHighPriority", UNSET)

        _network = d.pop("network", UNSET)
        network: list[VSphereReplicaJobNetworkMappingModel] | Unset = UNSET
        if _network is not UNSET:
            network = []
            for network_item_data in _network:
                network_item = VSphereReplicaJobNetworkMappingModel.from_dict(network_item_data)

                network.append(network_item)

        _re_ip = d.pop("reIp", UNSET)
        re_ip: ReplicaJobReIpRulesModel | Unset
        if isinstance(_re_ip, Unset):
            re_ip = UNSET
        else:
            re_ip = ReplicaJobReIpRulesModel.from_dict(_re_ip)

        _job_settings = d.pop("jobSettings", UNSET)
        job_settings: VSphereReplicaJobSettingsModel | Unset
        if isinstance(_job_settings, Unset):
            job_settings = UNSET
        else:
            job_settings = VSphereReplicaJobSettingsModel.from_dict(_job_settings)

        _data_transfer = d.pop("dataTransfer", UNSET)
        data_transfer: VSphereReplicaJobDataTransferModel | Unset
        if isinstance(_data_transfer, Unset):
            data_transfer = UNSET
        else:
            data_transfer = VSphereReplicaJobDataTransferModel.from_dict(_data_transfer)

        _seeding = d.pop("seeding", UNSET)
        seeding: VSphereReplicaSeedingModel | Unset
        if isinstance(_seeding, Unset):
            seeding = UNSET
        else:
            seeding = VSphereReplicaSeedingModel.from_dict(_seeding)

        _guest_processing = d.pop("guestProcessing", UNSET)
        guest_processing: ReplicaJobGuestProcessingModel | Unset
        if isinstance(_guest_processing, Unset):
            guest_processing = UNSET
        else:
            guest_processing = ReplicaJobGuestProcessingModel.from_dict(_guest_processing)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        v_sphere_replica_job_spec = cls(
            name=name,
            type_=type_,
            description=description,
            virtual_machines=virtual_machines,
            destination=destination,
            is_high_priority=is_high_priority,
            network=network,
            re_ip=re_ip,
            job_settings=job_settings,
            data_transfer=data_transfer,
            seeding=seeding,
            guest_processing=guest_processing,
            schedule=schedule,
        )

        v_sphere_replica_job_spec.additional_properties = d
        return v_sphere_replica_job_spec

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
