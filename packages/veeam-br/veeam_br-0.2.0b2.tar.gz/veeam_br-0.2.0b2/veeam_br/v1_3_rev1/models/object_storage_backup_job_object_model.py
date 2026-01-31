from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_backup_job_tag_mask_model import ObjectStorageBackupJobTagMaskModel


T = TypeVar("T", bound="ObjectStorageBackupJobObjectModel")


@_attrs_define
class ObjectStorageBackupJobObjectModel:
    """Objects processed by the backup job.

    Attributes:
        object_storage_server_id (UUID): ID of the object storage server. To get the ID, run the [Get All Unstructured
            Data Servers](Inventory-Browser#operation/GetAllUnstructuredDataServers) request.
        container (str | Unset): Bucket or container that will be processed by the backup job.
        path (str | Unset): Object path or prefixes within a bucket or a container.
        inclusion_tag_mask (list[ObjectStorageBackupJobTagMaskModel] | Unset): Array of objects added to the object
            storage backup job. Full paths to files and folders, environmental variables and file masks with the asterisk
            (*) and question mark (?) characters can be used.
        exclusion_tag_mask (list[ObjectStorageBackupJobTagMaskModel] | Unset): Array of objects excluded from the object
            storage backup job. Full paths to files and folders, environmental variables and file masks with the asterisk
            (*) and question mark (?) characters can be used.
        exclusion_path_mask (list[str] | Unset): Array of paths to files excluded from the object storage backup job.
            Full paths to files and folders, environmental variables and file masks with the asterisk (*) and question mark
            (?) characters can be used.
    """

    object_storage_server_id: UUID
    container: str | Unset = UNSET
    path: str | Unset = UNSET
    inclusion_tag_mask: list[ObjectStorageBackupJobTagMaskModel] | Unset = UNSET
    exclusion_tag_mask: list[ObjectStorageBackupJobTagMaskModel] | Unset = UNSET
    exclusion_path_mask: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        object_storage_server_id = str(self.object_storage_server_id)

        container = self.container

        path = self.path

        inclusion_tag_mask: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.inclusion_tag_mask, Unset):
            inclusion_tag_mask = []
            for inclusion_tag_mask_item_data in self.inclusion_tag_mask:
                inclusion_tag_mask_item = inclusion_tag_mask_item_data.to_dict()
                inclusion_tag_mask.append(inclusion_tag_mask_item)

        exclusion_tag_mask: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.exclusion_tag_mask, Unset):
            exclusion_tag_mask = []
            for exclusion_tag_mask_item_data in self.exclusion_tag_mask:
                exclusion_tag_mask_item = exclusion_tag_mask_item_data.to_dict()
                exclusion_tag_mask.append(exclusion_tag_mask_item)

        exclusion_path_mask: list[str] | Unset = UNSET
        if not isinstance(self.exclusion_path_mask, Unset):
            exclusion_path_mask = self.exclusion_path_mask

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "objectStorageServerId": object_storage_server_id,
            }
        )
        if container is not UNSET:
            field_dict["container"] = container
        if path is not UNSET:
            field_dict["path"] = path
        if inclusion_tag_mask is not UNSET:
            field_dict["inclusionTagMask"] = inclusion_tag_mask
        if exclusion_tag_mask is not UNSET:
            field_dict["exclusionTagMask"] = exclusion_tag_mask
        if exclusion_path_mask is not UNSET:
            field_dict["exclusionPathMask"] = exclusion_path_mask

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_backup_job_tag_mask_model import ObjectStorageBackupJobTagMaskModel

        d = dict(src_dict)
        object_storage_server_id = UUID(d.pop("objectStorageServerId"))

        container = d.pop("container", UNSET)

        path = d.pop("path", UNSET)

        _inclusion_tag_mask = d.pop("inclusionTagMask", UNSET)
        inclusion_tag_mask: list[ObjectStorageBackupJobTagMaskModel] | Unset = UNSET
        if _inclusion_tag_mask is not UNSET:
            inclusion_tag_mask = []
            for inclusion_tag_mask_item_data in _inclusion_tag_mask:
                inclusion_tag_mask_item = ObjectStorageBackupJobTagMaskModel.from_dict(inclusion_tag_mask_item_data)

                inclusion_tag_mask.append(inclusion_tag_mask_item)

        _exclusion_tag_mask = d.pop("exclusionTagMask", UNSET)
        exclusion_tag_mask: list[ObjectStorageBackupJobTagMaskModel] | Unset = UNSET
        if _exclusion_tag_mask is not UNSET:
            exclusion_tag_mask = []
            for exclusion_tag_mask_item_data in _exclusion_tag_mask:
                exclusion_tag_mask_item = ObjectStorageBackupJobTagMaskModel.from_dict(exclusion_tag_mask_item_data)

                exclusion_tag_mask.append(exclusion_tag_mask_item)

        exclusion_path_mask = cast(list[str], d.pop("exclusionPathMask", UNSET))

        object_storage_backup_job_object_model = cls(
            object_storage_server_id=object_storage_server_id,
            container=container,
            path=path,
            inclusion_tag_mask=inclusion_tag_mask,
            exclusion_tag_mask=exclusion_tag_mask,
            exclusion_path_mask=exclusion_path_mask,
        )

        object_storage_backup_job_object_model.additional_properties = d
        return object_storage_backup_job_object_model

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
