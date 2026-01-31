from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.unstructured_data_share_restore_destination_model import UnstructuredDataShareRestoreDestinationModel
    from ..models.unstructured_data_share_restore_options_model import UnstructuredDataShareRestoreOptionsModel


T = TypeVar("T", bound="UnstructuredDataEntireShareRestoreSpec")


@_attrs_define
class UnstructuredDataEntireShareRestoreSpec:
    """Settings for restoring entire file share.

    Attributes:
        restore_point_id (UUID): Restore point ID. To get the ID, run the [Get All Restore Points](Restore-
            Points#operation/GetAllObjectRestorePoints) request.
        destination (UnstructuredDataShareRestoreDestinationModel | Unset): Target for restoring entire file share.
        restore_options (UnstructuredDataShareRestoreOptionsModel | Unset): Restore options for restoring entire file
            share.
    """

    restore_point_id: UUID
    destination: UnstructuredDataShareRestoreDestinationModel | Unset = UNSET
    restore_options: UnstructuredDataShareRestoreOptionsModel | Unset = UNSET
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
        from ..models.unstructured_data_share_restore_destination_model import (
            UnstructuredDataShareRestoreDestinationModel,
        )
        from ..models.unstructured_data_share_restore_options_model import UnstructuredDataShareRestoreOptionsModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        _destination = d.pop("destination", UNSET)
        destination: UnstructuredDataShareRestoreDestinationModel | Unset
        if isinstance(_destination, Unset):
            destination = UNSET
        else:
            destination = UnstructuredDataShareRestoreDestinationModel.from_dict(_destination)

        _restore_options = d.pop("restoreOptions", UNSET)
        restore_options: UnstructuredDataShareRestoreOptionsModel | Unset
        if isinstance(_restore_options, Unset):
            restore_options = UNSET
        else:
            restore_options = UnstructuredDataShareRestoreOptionsModel.from_dict(_restore_options)

        unstructured_data_entire_share_restore_spec = cls(
            restore_point_id=restore_point_id,
            destination=destination,
            restore_options=restore_options,
        )

        unstructured_data_entire_share_restore_spec.additional_properties = d
        return unstructured_data_entire_share_restore_spec

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
