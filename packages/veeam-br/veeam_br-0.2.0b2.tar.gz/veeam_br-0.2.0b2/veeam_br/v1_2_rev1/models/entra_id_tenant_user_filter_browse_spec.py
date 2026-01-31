from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantUserFilterBrowseSpec")


@_attrs_define
class EntraIdTenantUserFilterBrowseSpec:
    """Filtering options.

    Attributes:
        display_name (str | Unset): User display name.
        mail_address (str | Unset): User email address.
        user_name (str | Unset): User principal name.
        user_type (str | Unset): User type.
        employee_type (str | Unset): Employee type.
        account_enabled (bool | Unset): If `true`, the user account is enabled.
        company_name (str | Unset): Company name.
        creation_type (str | Unset): Creation type.
        department (str | Unset): Company department.
        country (str | Unset): Country or region.
        job_title (str | Unset): Job title.
        office_location (str | Unset): Office location.
    """

    display_name: str | Unset = UNSET
    mail_address: str | Unset = UNSET
    user_name: str | Unset = UNSET
    user_type: str | Unset = UNSET
    employee_type: str | Unset = UNSET
    account_enabled: bool | Unset = UNSET
    company_name: str | Unset = UNSET
    creation_type: str | Unset = UNSET
    department: str | Unset = UNSET
    country: str | Unset = UNSET
    job_title: str | Unset = UNSET
    office_location: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        mail_address = self.mail_address

        user_name = self.user_name

        user_type = self.user_type

        employee_type = self.employee_type

        account_enabled = self.account_enabled

        company_name = self.company_name

        creation_type = self.creation_type

        department = self.department

        country = self.country

        job_title = self.job_title

        office_location = self.office_location

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if mail_address is not UNSET:
            field_dict["mailAddress"] = mail_address
        if user_name is not UNSET:
            field_dict["userName"] = user_name
        if user_type is not UNSET:
            field_dict["userType"] = user_type
        if employee_type is not UNSET:
            field_dict["employeeType"] = employee_type
        if account_enabled is not UNSET:
            field_dict["accountEnabled"] = account_enabled
        if company_name is not UNSET:
            field_dict["companyName"] = company_name
        if creation_type is not UNSET:
            field_dict["creationType"] = creation_type
        if department is not UNSET:
            field_dict["department"] = department
        if country is not UNSET:
            field_dict["country"] = country
        if job_title is not UNSET:
            field_dict["jobTitle"] = job_title
        if office_location is not UNSET:
            field_dict["officeLocation"] = office_location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        mail_address = d.pop("mailAddress", UNSET)

        user_name = d.pop("userName", UNSET)

        user_type = d.pop("userType", UNSET)

        employee_type = d.pop("employeeType", UNSET)

        account_enabled = d.pop("accountEnabled", UNSET)

        company_name = d.pop("companyName", UNSET)

        creation_type = d.pop("creationType", UNSET)

        department = d.pop("department", UNSET)

        country = d.pop("country", UNSET)

        job_title = d.pop("jobTitle", UNSET)

        office_location = d.pop("officeLocation", UNSET)

        entra_id_tenant_user_filter_browse_spec = cls(
            display_name=display_name,
            mail_address=mail_address,
            user_name=user_name,
            user_type=user_type,
            employee_type=employee_type,
            account_enabled=account_enabled,
            company_name=company_name,
            creation_type=creation_type,
            department=department,
            country=country,
            job_title=job_title,
            office_location=office_location,
        )

        entra_id_tenant_user_filter_browse_spec.additional_properties = d
        return entra_id_tenant_user_filter_browse_spec

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
