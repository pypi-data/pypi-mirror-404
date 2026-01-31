from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GuestInteractionProxiesSettingsImportModel")


@_attrs_define
class GuestInteractionProxiesSettingsImportModel:
    """Guest interaction proxy used to deploy the runtime process on the VM guest OS.

    Attributes:
        automatic_selection (bool): If `true`, Veeam Backup & Replication automatically selects the guest interaction
            proxy. Default: True.
        proxies (list[str] | Unset): Array of proxies specified explicitly. The array must contain Microsoft Windows
            servers added to the backup infrastructure only.
    """

    automatic_selection: bool = True
    proxies: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        automatic_selection = self.automatic_selection

        proxies: list[str] | Unset = UNSET
        if not isinstance(self.proxies, Unset):
            proxies = self.proxies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "automaticSelection": automatic_selection,
            }
        )
        if proxies is not UNSET:
            field_dict["proxies"] = proxies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        automatic_selection = d.pop("automaticSelection")

        proxies = cast(list[str], d.pop("proxies", UNSET))

        guest_interaction_proxies_settings_import_model = cls(
            automatic_selection=automatic_selection,
            proxies=proxies,
        )

        guest_interaction_proxies_settings_import_model.additional_properties = d
        return guest_interaction_proxies_settings_import_model

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
