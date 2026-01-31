from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_content_mount_state import EBackupContentMountState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_content_publication_info import BackupContentPublicationInfo


T = TypeVar("T", bound="BackupContentMountModel")


@_attrs_define
class BackupContentMountModel:
    """Details about the mount point.

    Attributes:
        id (UUID | Unset): Mount point ID.
        initiator_name (str | Unset): Account used to publish the disks.
        backup_id (UUID | Unset): Backup ID.
        backup_name (str | Unset): Backup name.
        restore_point_id (UUID | Unset): Restore point ID.
        restore_point_name (str | Unset): Restore point name.
        mount_state (EBackupContentMountState | Unset): Mount state.
        info (BackupContentPublicationInfo | Unset): Details about the publishing operation.
    """

    id: UUID | Unset = UNSET
    initiator_name: str | Unset = UNSET
    backup_id: UUID | Unset = UNSET
    backup_name: str | Unset = UNSET
    restore_point_id: UUID | Unset = UNSET
    restore_point_name: str | Unset = UNSET
    mount_state: EBackupContentMountState | Unset = UNSET
    info: BackupContentPublicationInfo | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        initiator_name = self.initiator_name

        backup_id: str | Unset = UNSET
        if not isinstance(self.backup_id, Unset):
            backup_id = str(self.backup_id)

        backup_name = self.backup_name

        restore_point_id: str | Unset = UNSET
        if not isinstance(self.restore_point_id, Unset):
            restore_point_id = str(self.restore_point_id)

        restore_point_name = self.restore_point_name

        mount_state: str | Unset = UNSET
        if not isinstance(self.mount_state, Unset):
            mount_state = self.mount_state.value

        info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.info, Unset):
            info = self.info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if initiator_name is not UNSET:
            field_dict["initiatorName"] = initiator_name
        if backup_id is not UNSET:
            field_dict["backupId"] = backup_id
        if backup_name is not UNSET:
            field_dict["backupName"] = backup_name
        if restore_point_id is not UNSET:
            field_dict["restorePointId"] = restore_point_id
        if restore_point_name is not UNSET:
            field_dict["restorePointName"] = restore_point_name
        if mount_state is not UNSET:
            field_dict["mountState"] = mount_state
        if info is not UNSET:
            field_dict["info"] = info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_content_publication_info import BackupContentPublicationInfo

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        initiator_name = d.pop("initiatorName", UNSET)

        _backup_id = d.pop("backupId", UNSET)
        backup_id: UUID | Unset
        if isinstance(_backup_id, Unset):
            backup_id = UNSET
        else:
            backup_id = UUID(_backup_id)

        backup_name = d.pop("backupName", UNSET)

        _restore_point_id = d.pop("restorePointId", UNSET)
        restore_point_id: UUID | Unset
        if isinstance(_restore_point_id, Unset):
            restore_point_id = UNSET
        else:
            restore_point_id = UUID(_restore_point_id)

        restore_point_name = d.pop("restorePointName", UNSET)

        _mount_state = d.pop("mountState", UNSET)
        mount_state: EBackupContentMountState | Unset
        if isinstance(_mount_state, Unset):
            mount_state = UNSET
        else:
            mount_state = EBackupContentMountState(_mount_state)

        _info = d.pop("info", UNSET)
        info: BackupContentPublicationInfo | Unset
        if isinstance(_info, Unset):
            info = UNSET
        else:
            info = BackupContentPublicationInfo.from_dict(_info)

        backup_content_mount_model = cls(
            id=id,
            initiator_name=initiator_name,
            backup_id=backup_id,
            backup_name=backup_name,
            restore_point_id=restore_point_id,
            restore_point_name=restore_point_name,
            mount_state=mount_state,
            info=info,
        )

        backup_content_mount_model.additional_properties = d
        return backup_content_mount_model

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
