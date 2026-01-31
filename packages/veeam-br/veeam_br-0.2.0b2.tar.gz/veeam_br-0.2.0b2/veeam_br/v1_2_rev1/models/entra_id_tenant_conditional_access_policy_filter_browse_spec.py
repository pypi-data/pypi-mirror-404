from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_conditional_access_policy_state import EEntraIdTenantConditionalAccessPolicyState
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantConditionalAccessPolicyFilterBrowseSpec")


@_attrs_define
class EntraIdTenantConditionalAccessPolicyFilterBrowseSpec:
    """Filtering options.

    Attributes:
        display_name (str | Unset): Display name of the conditional access policy.
        state (list[EEntraIdTenantConditionalAccessPolicyState] | Unset):
    """

    display_name: str | Unset = UNSET
    state: list[EEntraIdTenantConditionalAccessPolicyState] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        state: list[str] | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = []
            for state_item_data in self.state:
                state_item = state_item_data.value
                state.append(state_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName", UNSET)

        _state = d.pop("state", UNSET)
        state: list[EEntraIdTenantConditionalAccessPolicyState] | Unset = UNSET
        if _state is not UNSET:
            state = []
            for state_item_data in _state:
                state_item = EEntraIdTenantConditionalAccessPolicyState(state_item_data)

                state.append(state_item)

        entra_id_tenant_conditional_access_policy_filter_browse_spec = cls(
            display_name=display_name,
            state=state,
        )

        entra_id_tenant_conditional_access_policy_filter_browse_spec.additional_properties = d
        return entra_id_tenant_conditional_access_policy_filter_browse_spec

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
