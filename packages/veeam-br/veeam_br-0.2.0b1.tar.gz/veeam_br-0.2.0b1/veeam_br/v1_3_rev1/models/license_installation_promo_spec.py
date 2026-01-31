from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseInstallationPromoSpec")


@_attrs_define
class LicenseInstallationPromoSpec:
    """Promo license installation settings.

    Attributes:
        overwrite_existing (bool | Unset): If `true`, the existing license is overwritten.
        enable_auto_update (bool | Unset): If `true`, the license is automatically updated.
        install_without_promo (bool | Unset): If `true`, the Promo license is installed without granting the Promo
            instances.
    """

    overwrite_existing: bool | Unset = UNSET
    enable_auto_update: bool | Unset = UNSET
    install_without_promo: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        overwrite_existing = self.overwrite_existing

        enable_auto_update = self.enable_auto_update

        install_without_promo = self.install_without_promo

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if overwrite_existing is not UNSET:
            field_dict["overwriteExisting"] = overwrite_existing
        if enable_auto_update is not UNSET:
            field_dict["enableAutoUpdate"] = enable_auto_update
        if install_without_promo is not UNSET:
            field_dict["installWithoutPromo"] = install_without_promo

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        overwrite_existing = d.pop("overwriteExisting", UNSET)

        enable_auto_update = d.pop("enableAutoUpdate", UNSET)

        install_without_promo = d.pop("installWithoutPromo", UNSET)

        license_installation_promo_spec = cls(
            overwrite_existing=overwrite_existing,
            enable_auto_update=enable_auto_update,
            install_without_promo=install_without_promo,
        )

        license_installation_promo_spec.additional_properties = d
        return license_installation_promo_spec

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
