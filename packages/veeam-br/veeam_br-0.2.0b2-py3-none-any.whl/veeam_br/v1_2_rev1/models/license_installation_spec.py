from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.license_installation_promo_spec import LicenseInstallationPromoSpec


T = TypeVar("T", bound="LicenseInstallationSpec")


@_attrs_define
class LicenseInstallationSpec:
    """Install license.

    Attributes:
        license_ (str): Base64-encoded string of the content of a license file.
        force_standalone_mode (bool | Unset): This property is only used with backup servers managed by Veeam Backup
            Enterprise Manager.<ul><li>If `true`, the request will install the license.</li><li>If `false` or the property
            is not specified, the request will produce an error, warning you that the backup server is managed by Enterprise
            Manager.</li></ul>
        promo (LicenseInstallationPromoSpec | Unset): Promo license settings.
    """

    license_: str
    force_standalone_mode: bool | Unset = UNSET
    promo: LicenseInstallationPromoSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        license_ = self.license_

        force_standalone_mode = self.force_standalone_mode

        promo: dict[str, Any] | Unset = UNSET
        if not isinstance(self.promo, Unset):
            promo = self.promo.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "license": license_,
            }
        )
        if force_standalone_mode is not UNSET:
            field_dict["forceStandaloneMode"] = force_standalone_mode
        if promo is not UNSET:
            field_dict["promo"] = promo

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.license_installation_promo_spec import LicenseInstallationPromoSpec

        d = dict(src_dict)
        license_ = d.pop("license")

        force_standalone_mode = d.pop("forceStandaloneMode", UNSET)

        _promo = d.pop("promo", UNSET)
        promo: LicenseInstallationPromoSpec | Unset
        if isinstance(_promo, Unset):
            promo = UNSET
        else:
            promo = LicenseInstallationPromoSpec.from_dict(_promo)

        license_installation_spec = cls(
            license_=license_,
            force_standalone_mode=force_standalone_mode,
            promo=promo,
        )

        license_installation_spec.additional_properties = d
        return license_installation_spec

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
