from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_restore_mode_type import EFlrRestoreModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flr_restore_target_host_model import FlrRestoreTargetHostModel


T = TypeVar("T", bound="FlrRestoreCredentialsValidationSpec")


@_attrs_define
class FlrRestoreCredentialsValidationSpec:
    """Settings for credentials validation for the target machine for the file-level restore.

    Attributes:
        restore_mode (EFlrRestoreModeType): Restore mode for file-level restore.
        credentials_id (UUID | Unset): ID of a credentials record used to connect to the target machine. If the ID is
            not specified, Veeam Backup & Replication will try to find credentials for the target machine in the stored
            credential records.
        target_host (FlrRestoreTargetHostModel | Unset): Target machine. To get an inventory object, run the [Get
            Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
    """

    restore_mode: EFlrRestoreModeType
    credentials_id: UUID | Unset = UNSET
    target_host: FlrRestoreTargetHostModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_mode = self.restore_mode.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        target_host: dict[str, Any] | Unset = UNSET
        if not isinstance(self.target_host, Unset):
            target_host = self.target_host.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restoreMode": restore_mode,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if target_host is not UNSET:
            field_dict["targetHost"] = target_host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flr_restore_target_host_model import FlrRestoreTargetHostModel

        d = dict(src_dict)
        restore_mode = EFlrRestoreModeType(d.pop("restoreMode"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _target_host = d.pop("targetHost", UNSET)
        target_host: FlrRestoreTargetHostModel | Unset
        if isinstance(_target_host, Unset):
            target_host = UNSET
        else:
            target_host = FlrRestoreTargetHostModel.from_dict(_target_host)

        flr_restore_credentials_validation_spec = cls(
            restore_mode=restore_mode,
            credentials_id=credentials_id,
            target_host=target_host,
        )

        flr_restore_credentials_validation_spec.additional_properties = d
        return flr_restore_credentials_validation_spec

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
