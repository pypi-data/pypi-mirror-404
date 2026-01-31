from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.proxy_datastore_model import ProxyDatastoreModel


T = TypeVar("T", bound="ProxyDatastoreSettingsModel")


@_attrs_define
class ProxyDatastoreSettingsModel:
    """Datastores to which the backup proxy has a direct SAN or NFS connection.

    Attributes:
        auto_select_enabled (bool): If `true`, all datastores that the backup proxy can access are detected
            automatically.
        datastores (list[ProxyDatastoreModel] | Unset): Array of datastores to which the backup proxy has a direct SAN
            or NFS connection.
    """

    auto_select_enabled: bool
    datastores: list[ProxyDatastoreModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_select_enabled = self.auto_select_enabled

        datastores: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.datastores, Unset):
            datastores = []
            for datastores_item_data in self.datastores:
                datastores_item = datastores_item_data.to_dict()
                datastores.append(datastores_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "autoSelectEnabled": auto_select_enabled,
            }
        )
        if datastores is not UNSET:
            field_dict["datastores"] = datastores

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.proxy_datastore_model import ProxyDatastoreModel

        d = dict(src_dict)
        auto_select_enabled = d.pop("autoSelectEnabled")

        _datastores = d.pop("datastores", UNSET)
        datastores: list[ProxyDatastoreModel] | Unset = UNSET
        if _datastores is not UNSET:
            datastores = []
            for datastores_item_data in _datastores:
                datastores_item = ProxyDatastoreModel.from_dict(datastores_item_data)

                datastores.append(datastores_item)

        proxy_datastore_settings_model = cls(
            auto_select_enabled=auto_select_enabled,
            datastores=datastores,
        )

        proxy_datastore_settings_model.additional_properties = d
        return proxy_datastore_settings_model

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
