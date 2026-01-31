from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_encryption_state import EBackupEncryptionState
from ..models.e_platform_type import EPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EC2BackupObjectModel")


@_attrs_define
class EC2BackupObjectModel:
    """AWS E2 backup object.

    Attributes:
        id (UUID): ID of the object.
        platform_name (EPlatformType): Platform type.
        object_id (str): ID of the virtual infrastructure object
        name (str | Unset): Name of the object.
        type_ (str | Unset): Type of the object.
        platform_id (UUID | Unset): ID of the platform where the object was created. The value is always
            *00000000-0000-0000-0000-000000000000* except for custom platforms.
        restore_points_count (int | Unset): Number of restore points.
        last_run_failed (bool | Unset): If `true`, the last run of the backup job failed.
        encryption_state (EBackupEncryptionState | Unset): Encryption state.
        path (str | Unset): Path to the object.
        owner (str | Unset): Owner of the object.
    """

    id: UUID
    platform_name: EPlatformType
    object_id: str
    name: str | Unset = UNSET
    type_: str | Unset = UNSET
    platform_id: UUID | Unset = UNSET
    restore_points_count: int | Unset = UNSET
    last_run_failed: bool | Unset = UNSET
    encryption_state: EBackupEncryptionState | Unset = UNSET
    path: str | Unset = UNSET
    owner: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        platform_name = self.platform_name.value

        object_id = self.object_id

        name = self.name

        type_ = self.type_

        platform_id: str | Unset = UNSET
        if not isinstance(self.platform_id, Unset):
            platform_id = str(self.platform_id)

        restore_points_count = self.restore_points_count

        last_run_failed = self.last_run_failed

        encryption_state: str | Unset = UNSET
        if not isinstance(self.encryption_state, Unset):
            encryption_state = self.encryption_state.value

        path = self.path

        owner = self.owner

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "platformName": platform_name,
                "objectId": object_id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if platform_id is not UNSET:
            field_dict["platformId"] = platform_id
        if restore_points_count is not UNSET:
            field_dict["restorePointsCount"] = restore_points_count
        if last_run_failed is not UNSET:
            field_dict["lastRunFailed"] = last_run_failed
        if encryption_state is not UNSET:
            field_dict["encryptionState"] = encryption_state
        if path is not UNSET:
            field_dict["path"] = path
        if owner is not UNSET:
            field_dict["owner"] = owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        platform_name = EPlatformType(d.pop("platformName"))

        object_id = d.pop("objectId")

        name = d.pop("name", UNSET)

        type_ = d.pop("type", UNSET)

        _platform_id = d.pop("platformId", UNSET)
        platform_id: UUID | Unset
        if isinstance(_platform_id, Unset):
            platform_id = UNSET
        else:
            platform_id = UUID(_platform_id)

        restore_points_count = d.pop("restorePointsCount", UNSET)

        last_run_failed = d.pop("lastRunFailed", UNSET)

        _encryption_state = d.pop("encryptionState", UNSET)
        encryption_state: EBackupEncryptionState | Unset
        if isinstance(_encryption_state, Unset):
            encryption_state = UNSET
        else:
            encryption_state = EBackupEncryptionState(_encryption_state)

        path = d.pop("path", UNSET)

        owner = d.pop("owner", UNSET)

        ec2_backup_object_model = cls(
            id=id,
            platform_name=platform_name,
            object_id=object_id,
            name=name,
            type_=type_,
            platform_id=platform_id,
            restore_points_count=restore_points_count,
            last_run_failed=last_run_failed,
            encryption_state=encryption_state,
            path=path,
            owner=owner,
        )

        ec2_backup_object_model.additional_properties = d
        return ec2_backup_object_model

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
