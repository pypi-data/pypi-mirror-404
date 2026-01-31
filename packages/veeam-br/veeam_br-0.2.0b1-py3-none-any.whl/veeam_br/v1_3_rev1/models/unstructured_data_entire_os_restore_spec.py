from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_os_restore_destination_model import UnstructuredDataOSRestoreDestinationModel
    from ..models.unstructured_data_os_restore_options_model import UnstructuredDataOSRestoreOptionsModel


T = TypeVar("T", bound="UnstructuredDataEntireOSRestoreSpec")


@_attrs_define
class UnstructuredDataEntireOSRestoreSpec:
    """Settings for restoring entire object storage bucket or container.

    Attributes:
        restore_point_id (UUID): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        destination (UnstructuredDataOSRestoreDestinationModel | Unset): Target for restoring entire object storage
            bucket or container.
        restore_options (UnstructuredDataOSRestoreOptionsModel | Unset): Restore options for restoring entire object
            storage bucket or container.
    """

    restore_point_id: UUID
    destination: UnstructuredDataOSRestoreDestinationModel | Unset = UNSET
    restore_options: UnstructuredDataOSRestoreOptionsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        destination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.destination, Unset):
            destination = self.destination.to_dict()

        restore_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.restore_options, Unset):
            restore_options = self.restore_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
            }
        )
        if destination is not UNSET:
            field_dict["destination"] = destination
        if restore_options is not UNSET:
            field_dict["restoreOptions"] = restore_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unstructured_data_os_restore_destination_model import UnstructuredDataOSRestoreDestinationModel
        from ..models.unstructured_data_os_restore_options_model import UnstructuredDataOSRestoreOptionsModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        _destination = d.pop("destination", UNSET)
        destination: UnstructuredDataOSRestoreDestinationModel | Unset
        if isinstance(_destination, Unset):
            destination = UNSET
        else:
            destination = UnstructuredDataOSRestoreDestinationModel.from_dict(_destination)

        _restore_options = d.pop("restoreOptions", UNSET)
        restore_options: UnstructuredDataOSRestoreOptionsModel | Unset
        if isinstance(_restore_options, Unset):
            restore_options = UNSET
        else:
            restore_options = UnstructuredDataOSRestoreOptionsModel.from_dict(_restore_options)

        unstructured_data_entire_os_restore_spec = cls(
            restore_point_id=restore_point_id,
            destination=destination,
            restore_options=restore_options,
        )

        unstructured_data_entire_os_restore_spec.additional_properties = d
        return unstructured_data_entire_os_restore_spec

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
