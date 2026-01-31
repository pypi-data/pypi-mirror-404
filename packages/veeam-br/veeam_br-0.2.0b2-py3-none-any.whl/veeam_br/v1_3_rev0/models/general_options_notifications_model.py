from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GeneralOptionsNotificationsModel")


@_attrs_define
class GeneralOptionsNotificationsModel:
    """Other notifications such as notifications on low disk space, support contract expiration, and available updates.

    Attributes:
        storage_space_threshold_enabled (bool): If `true`, notifications about critical amount of free space in backup
            storage are enabled.
        datastore_space_threshold_enabled (bool): If `true`, notifications about critical amount of free space in
            production datastore are enabled.
        skip_vm_space_threshold_enabled (bool): If `true` and the `skipVMSpaceThreshold` threshold is reached, Veeam
            Backup & Replication terminates backup and replication jobs working with production datastores before VM
            snapshots are taken.
        notify_on_support_expiration (bool): If `true`, notifications about support contract expiration are enabled.
        notify_on_updates (bool): If `true`, notifications about updates are enabled.
        storage_space_threshold (int | Unset): Space threshold of backup storage, in percent.
        datastore_space_threshold (int | Unset): Space threshold of production datastore, in percent.
        skip_vm_space_threshold (int | Unset): Space threshold of production datastore, in percent.
    """

    storage_space_threshold_enabled: bool
    datastore_space_threshold_enabled: bool
    skip_vm_space_threshold_enabled: bool
    notify_on_support_expiration: bool
    notify_on_updates: bool
    storage_space_threshold: int | Unset = UNSET
    datastore_space_threshold: int | Unset = UNSET
    skip_vm_space_threshold: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage_space_threshold_enabled = self.storage_space_threshold_enabled

        datastore_space_threshold_enabled = self.datastore_space_threshold_enabled

        skip_vm_space_threshold_enabled = self.skip_vm_space_threshold_enabled

        notify_on_support_expiration = self.notify_on_support_expiration

        notify_on_updates = self.notify_on_updates

        storage_space_threshold = self.storage_space_threshold

        datastore_space_threshold = self.datastore_space_threshold

        skip_vm_space_threshold = self.skip_vm_space_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "storageSpaceThresholdEnabled": storage_space_threshold_enabled,
                "datastoreSpaceThresholdEnabled": datastore_space_threshold_enabled,
                "skipVMSpaceThresholdEnabled": skip_vm_space_threshold_enabled,
                "notifyOnSupportExpiration": notify_on_support_expiration,
                "notifyOnUpdates": notify_on_updates,
            }
        )
        if storage_space_threshold is not UNSET:
            field_dict["storageSpaceThreshold"] = storage_space_threshold
        if datastore_space_threshold is not UNSET:
            field_dict["datastoreSpaceThreshold"] = datastore_space_threshold
        if skip_vm_space_threshold is not UNSET:
            field_dict["skipVMSpaceThreshold"] = skip_vm_space_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        storage_space_threshold_enabled = d.pop("storageSpaceThresholdEnabled")

        datastore_space_threshold_enabled = d.pop("datastoreSpaceThresholdEnabled")

        skip_vm_space_threshold_enabled = d.pop("skipVMSpaceThresholdEnabled")

        notify_on_support_expiration = d.pop("notifyOnSupportExpiration")

        notify_on_updates = d.pop("notifyOnUpdates")

        storage_space_threshold = d.pop("storageSpaceThreshold", UNSET)

        datastore_space_threshold = d.pop("datastoreSpaceThreshold", UNSET)

        skip_vm_space_threshold = d.pop("skipVMSpaceThreshold", UNSET)

        general_options_notifications_model = cls(
            storage_space_threshold_enabled=storage_space_threshold_enabled,
            datastore_space_threshold_enabled=datastore_space_threshold_enabled,
            skip_vm_space_threshold_enabled=skip_vm_space_threshold_enabled,
            notify_on_support_expiration=notify_on_support_expiration,
            notify_on_updates=notify_on_updates,
            storage_space_threshold=storage_space_threshold,
            datastore_space_threshold=datastore_space_threshold,
            skip_vm_space_threshold=skip_vm_space_threshold,
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
