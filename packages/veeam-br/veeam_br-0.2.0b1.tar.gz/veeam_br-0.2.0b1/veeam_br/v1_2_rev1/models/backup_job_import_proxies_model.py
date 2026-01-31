from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_proxy_import_model import BackupProxyImportModel


T = TypeVar("T", bound="BackupJobImportProxiesModel")


@_attrs_define
class BackupJobImportProxiesModel:
    """Backup proxies.

    Attributes:
        automatic_selection (bool): If `true`, backup proxies are detected and assigned automatically. Default: True.
        proxies (list[BackupProxyImportModel] | Unset): Array of backup proxies.
    """

    automatic_selection: bool = True
    proxies: list[BackupProxyImportModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        automatic_selection = self.automatic_selection

        proxies: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.proxies, Unset):
            proxies = []
            for proxies_item_data in self.proxies:
                proxies_item = proxies_item_data.to_dict()
                proxies.append(proxies_item)

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
        from ..models.backup_proxy_import_model import BackupProxyImportModel

        d = dict(src_dict)
        automatic_selection = d.pop("automaticSelection")

        _proxies = d.pop("proxies", UNSET)
        proxies: list[BackupProxyImportModel] | Unset = UNSET
        if _proxies is not UNSET:
            proxies = []
            for proxies_item_data in _proxies:
                proxies_item = BackupProxyImportModel.from_dict(proxies_item_data)

                proxies.append(proxies_item)

        backup_job_import_proxies_model = cls(
            automatic_selection=automatic_selection,
            proxies=proxies,
        )

        backup_job_import_proxies_model.additional_properties = d
        return backup_job_import_proxies_model

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
