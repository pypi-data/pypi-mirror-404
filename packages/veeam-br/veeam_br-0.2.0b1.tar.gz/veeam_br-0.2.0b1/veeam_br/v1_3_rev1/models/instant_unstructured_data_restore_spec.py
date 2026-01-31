from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_restore_options_model import UnstructuredDataRestoreOptionsModel


T = TypeVar("T", bound="InstantUnstructuredDataRestoreSpec")


@_attrs_define
class InstantUnstructuredDataRestoreSpec:
    """Settings for Instant File Share Recovery.

    Attributes:
        restore_options (list[UnstructuredDataRestoreOptionsModel]): Array of options for Instant File Share Recovery.
        auto_select_mount_servers (bool | Unset): If `true`, Veeam Backup & Replication will assign the backup server as
            a mount server.
        reason (str | Unset): Reason for performing Instant Recovery.
    """

    restore_options: list[UnstructuredDataRestoreOptionsModel]
    auto_select_mount_servers: bool | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_options = []
        for restore_options_item_data in self.restore_options:
            restore_options_item = restore_options_item_data.to_dict()
            restore_options.append(restore_options_item)

        auto_select_mount_servers = self.auto_select_mount_servers

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restoreOptions": restore_options,
            }
        )
        if auto_select_mount_servers is not UNSET:
            field_dict["autoSelectMountServers"] = auto_select_mount_servers
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_restore_options_model import UnstructuredDataRestoreOptionsModel

        d = dict(src_dict)
        restore_options = []
        _restore_options = d.pop("restoreOptions")
        for restore_options_item_data in _restore_options:
            restore_options_item = UnstructuredDataRestoreOptionsModel.from_dict(restore_options_item_data)

            restore_options.append(restore_options_item)

        auto_select_mount_servers = d.pop("autoSelectMountServers", UNSET)

        reason = d.pop("reason", UNSET)

        instant_unstructured_data_restore_spec = cls(
            restore_options=restore_options,
            auto_select_mount_servers=auto_select_mount_servers,
            reason=reason,
        )

        instant_unstructured_data_restore_spec.additional_properties = d
        return instant_unstructured_data_restore_spec

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
