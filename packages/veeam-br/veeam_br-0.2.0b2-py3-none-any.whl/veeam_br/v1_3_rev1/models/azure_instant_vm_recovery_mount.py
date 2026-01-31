from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_instant_recovery_mount_state import EAzureInstantRecoveryMountState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_instant_vm_recovery_spec import AzureInstantVMRecoverySpec


T = TypeVar("T", bound="AzureInstantVMRecoveryMount")


@_attrs_define
class AzureInstantVMRecoveryMount:
    """Mount point for Instant Recovery to Microsoft Azure.

    Attributes:
        id (UUID): Mount point ID.
        state (EAzureInstantRecoveryMountState): Mount state.
        spec (AzureInstantVMRecoverySpec): Settings for Instant Recovery to Microsoft Azure.
        error_message (str | Unset): Error message.
    """

    id: UUID
    state: EAzureInstantRecoveryMountState
    spec: AzureInstantVMRecoverySpec
    error_message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        state = self.state.value

        spec = self.spec.to_dict()

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "state": state,
                "spec": spec,
            }
        )
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_instant_vm_recovery_spec import AzureInstantVMRecoverySpec

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        state = EAzureInstantRecoveryMountState(d.pop("state"))

        spec = AzureInstantVMRecoverySpec.from_dict(d.pop("spec"))

        error_message = d.pop("errorMessage", UNSET)

        azure_instant_vm_recovery_mount = cls(
            id=id,
            state=state,
            spec=spec,
            error_message=error_message,
        )

        azure_instant_vm_recovery_mount.additional_properties = d
        return azure_instant_vm_recovery_mount

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
