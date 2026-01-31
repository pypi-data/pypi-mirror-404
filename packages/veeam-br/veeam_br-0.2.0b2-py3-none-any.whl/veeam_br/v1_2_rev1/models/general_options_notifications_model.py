from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GeneralOptionsNotificationsModel")


@_attrs_define
class GeneralOptionsNotificationsModel:
    """Other notifications such as notifications on low disk space, support contract expiration, and available updates.

    Attributes:
        storage_space_threshold_enabled (bool): If `true`, notifications about critical amount of free space in backup
            storage are enabled.
        storage_space_threshold (int): Space threshold of backup storage, in percent.
        datastore_space_threshold_enabled (bool): If `true`, notifications about critical amount of free space in
            production datastore are enabled.
        datastore_space_threshold (int): Space threshold of production datastore, in percent.
        skip_vm_space_threshold_enabled (bool): If `true` and the `skipVMSpaceThreshold` threshold is reached, Veeam
            Backup & Replication terminates backup and replication jobs working with production datastores before VM
            snapshots are taken.
        skip_vm_space_threshold (int): Space threshold of production datastore, in percent.
        notify_on_support_expiration (bool): If `true`, notifications about support contract expiration are enabled.
        notify_on_updates (bool): If `true`, notifications about updates are enabled.
    """

    storage_space_threshold_enabled: bool
    storage_space_threshold: int
    datastore_space_threshold_enabled: bool
    datastore_space_threshold: int
    skip_vm_space_threshold_enabled: bool
    skip_vm_space_threshold: int
    notify_on_support_expiration: bool
    notify_on_updates: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage_space_threshold_enabled = self.storage_space_threshold_enabled

        storage_space_threshold = self.storage_space_threshold

        datastore_space_threshold_enabled = self.datastore_space_threshold_enabled

        datastore_space_threshold = self.datastore_space_threshold

        skip_vm_space_threshold_enabled = self.skip_vm_space_threshold_enabled

        skip_vm_space_threshold = self.skip_vm_space_threshold

        notify_on_support_expiration = self.notify_on_support_expiration

        notify_on_updates = self.notify_on_updates

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "storageSpaceThresholdEnabled": storage_space_threshold_enabled,
                "storageSpaceThreshold": storage_space_threshold,
                "datastoreSpaceThresholdEnabled": datastore_space_threshold_enabled,
                "datastoreSpaceThreshold": datastore_space_threshold,
                "skipVMSpaceThresholdEnabled": skip_vm_space_threshold_enabled,
                "skipVMSpaceThreshold": skip_vm_space_threshold,
                "notifyOnSupportExpiration": notify_on_support_expiration,
                "notifyOnUpdates": notify_on_updates,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        storage_space_threshold_enabled = d.pop("storageSpaceThresholdEnabled")

        storage_space_threshold = d.pop("storageSpaceThreshold")

        datastore_space_threshold_enabled = d.pop("datastoreSpaceThresholdEnabled")

        datastore_space_threshold = d.pop("datastoreSpaceThreshold")

        skip_vm_space_threshold_enabled = d.pop("skipVMSpaceThresholdEnabled")

        skip_vm_space_threshold = d.pop("skipVMSpaceThreshold")

        notify_on_support_expiration = d.pop("notifyOnSupportExpiration")

        notify_on_updates = d.pop("notifyOnUpdates")

        general_options_notifications_model = cls(
            storage_space_threshold_enabled=storage_space_threshold_enabled,
            storage_space_threshold=storage_space_threshold,
            datastore_space_threshold_enabled=datastore_space_threshold_enabled,
            datastore_space_threshold=datastore_space_threshold,
            skip_vm_space_threshold_enabled=skip_vm_space_threshold_enabled,
            skip_vm_space_threshold=skip_vm_space_threshold,
            notify_on_support_expiration=notify_on_support_expiration,
            notify_on_updates=notify_on_updates,
        )

        general_options_notifications_model.additional_properties = d
        return general_options_notifications_model

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
