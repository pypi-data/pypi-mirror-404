from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_data_transfer_model import EJobDataTransferModel
from ..types import UNSET, Unset

T = TypeVar("T", bound="WanAcceleratorSettingsModel")


@_attrs_define
class WanAcceleratorSettingsModel:
    """WAN accelerator settings.

    Attributes:
        transfer_mode (EJobDataTransferModel): Data transfer mode.
        source_wan_accelerator_id (UUID | Unset): ID of a WAN accelerator configured in the source site.
        target_wan_accelerator_id (UUID | Unset): ID of a WAN accelerator configured in the target site.
    """

    transfer_mode: EJobDataTransferModel
    source_wan_accelerator_id: UUID | Unset = UNSET
    target_wan_accelerator_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        transfer_mode = self.transfer_mode.value

        source_wan_accelerator_id: str | Unset = UNSET
        if not isinstance(self.source_wan_accelerator_id, Unset):
            source_wan_accelerator_id = str(self.source_wan_accelerator_id)

        target_wan_accelerator_id: str | Unset = UNSET
        if not isinstance(self.target_wan_accelerator_id, Unset):
            target_wan_accelerator_id = str(self.target_wan_accelerator_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "transferMode": transfer_mode,
            }
        )
        if source_wan_accelerator_id is not UNSET:
            field_dict["sourceWANAcceleratorId"] = source_wan_accelerator_id
        if target_wan_accelerator_id is not UNSET:
            field_dict["targetWANAcceleratorId"] = target_wan_accelerator_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        transfer_mode = EJobDataTransferModel(d.pop("transferMode"))

        _source_wan_accelerator_id = d.pop("sourceWANAcceleratorId", UNSET)
        source_wan_accelerator_id: UUID | Unset
        if isinstance(_source_wan_accelerator_id, Unset):
            source_wan_accelerator_id = UNSET
        else:
            source_wan_accelerator_id = UUID(_source_wan_accelerator_id)

        _target_wan_accelerator_id = d.pop("targetWANAcceleratorId", UNSET)
        target_wan_accelerator_id: UUID | Unset
        if isinstance(_target_wan_accelerator_id, Unset):
            target_wan_accelerator_id = UNSET
        else:
            target_wan_accelerator_id = UUID(_target_wan_accelerator_id)

        wan_accelerator_settings_model = cls(
            transfer_mode=transfer_mode,
            source_wan_accelerator_id=source_wan_accelerator_id,
            target_wan_accelerator_id=target_wan_accelerator_id,
        )

        wan_accelerator_settings_model.additional_properties = d
        return wan_accelerator_settings_model

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
