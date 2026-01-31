from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_repository_type import ERepositoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.scale_out_repository_details_model import ScaleOutRepositoryDetailsModel


T = TypeVar("T", bound="RepositoryStateModel")


@_attrs_define
class RepositoryStateModel:
    """Repository state.

    Attributes:
        id (UUID): Backup repository ID.
        name (str): Name of the backup repository.
        type_ (ERepositoryType): Repository type.
        description (str): Description of the backup repository.
        capacity_gb (float): Repository capacity in GB.
        free_gb (float): Free repository space in GB.
        used_space_gb (float): Used repository space in GB.
        is_online (bool): If `true`, the repository is online.
        is_out_of_date (bool): If `true`, the repository contains outdated components.
        host_id (UUID | Unset): ID of the server that is used as a backup repository.
        host_name (str | Unset): Name of the server that is used as a backup repository.
        path (str | Unset): Path to the folder where backup files are stored.
        scale_out_repository_details (ScaleOutRepositoryDetailsModel | Unset): Details related to scale-out backup
            repositories.
    """

    id: UUID
    name: str
    type_: ERepositoryType
    description: str
    capacity_gb: float
    free_gb: float
    used_space_gb: float
    is_online: bool
    is_out_of_date: bool
    host_id: UUID | Unset = UNSET
    host_name: str | Unset = UNSET
    path: str | Unset = UNSET
    scale_out_repository_details: ScaleOutRepositoryDetailsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        description = self.description

        capacity_gb = self.capacity_gb

        free_gb = self.free_gb

        used_space_gb = self.used_space_gb

        is_online = self.is_online

        is_out_of_date = self.is_out_of_date

        host_id: str | Unset = UNSET
        if not isinstance(self.host_id, Unset):
            host_id = str(self.host_id)

        host_name = self.host_name

        path = self.path

        scale_out_repository_details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scale_out_repository_details, Unset):
            scale_out_repository_details = self.scale_out_repository_details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "description": description,
                "capacityGB": capacity_gb,
                "freeGB": free_gb,
                "usedSpaceGB": used_space_gb,
                "isOnline": is_online,
                "isOutOfDate": is_out_of_date,
            }
        )
        if host_id is not UNSET:
            field_dict["hostId"] = host_id
        if host_name is not UNSET:
            field_dict["hostName"] = host_name
        if path is not UNSET:
            field_dict["path"] = path
        if scale_out_repository_details is not UNSET:
            field_dict["scaleOutRepositoryDetails"] = scale_out_repository_details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.scale_out_repository_details_model import ScaleOutRepositoryDetailsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = ERepositoryType(d.pop("type"))

        description = d.pop("description")

        capacity_gb = d.pop("capacityGB")

        free_gb = d.pop("freeGB")

        used_space_gb = d.pop("usedSpaceGB")

        is_online = d.pop("isOnline")

        is_out_of_date = d.pop("isOutOfDate")

        _host_id = d.pop("hostId", UNSET)
        host_id: UUID | Unset
        if isinstance(_host_id, Unset):
            host_id = UNSET
        else:
            host_id = UUID(_host_id)

        host_name = d.pop("hostName", UNSET)

        path = d.pop("path", UNSET)

        _scale_out_repository_details = d.pop("scaleOutRepositoryDetails", UNSET)
        scale_out_repository_details: ScaleOutRepositoryDetailsModel | Unset
        if isinstance(_scale_out_repository_details, Unset):
            scale_out_repository_details = UNSET
        else:
            scale_out_repository_details = ScaleOutRepositoryDetailsModel.from_dict(_scale_out_repository_details)

        repository_state_model = cls(
            id=id,
            name=name,
            type_=type_,
            description=description,
            capacity_gb=capacity_gb,
            free_gb=free_gb,
            used_space_gb=used_space_gb,
            is_online=is_online,
            is_out_of_date=is_out_of_date,
            host_id=host_id,
            host_name=host_name,
            path=path,
            scale_out_repository_details=scale_out_repository_details,
        )

        repository_state_model.additional_properties = d
        return repository_state_model

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
