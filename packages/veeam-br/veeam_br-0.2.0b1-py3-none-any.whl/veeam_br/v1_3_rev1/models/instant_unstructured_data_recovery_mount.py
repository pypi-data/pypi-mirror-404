from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_unstructured_data_instant_recovery_mount_state import EUnstructuredDataInstantRecoveryMountState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.instant_unstructured_data_restore_spec import InstantUnstructuredDataRestoreSpec


T = TypeVar("T", bound="InstantUnstructuredDataRecoveryMount")


@_attrs_define
class InstantUnstructuredDataRecoveryMount:
    """Settings of the Instant Recovery mount point of unstructured data.

    Attributes:
        id (UUID): Mount point ID. To get the ID, run the [Get All Mount Points for Instant File Share Recovery]
            (#/Restore/GetAllInstantUnstructuredDataRecoveryMounts) request.
        session_id (UUID): Restore session ID. Use the ID to track the progress. For details, see [Get
            Session](Sessions#operation/GetSession).
        state (EUnstructuredDataInstantRecoveryMountState): Mount state.
        spec (InstantUnstructuredDataRestoreSpec): Settings for Instant File Share Recovery.
        unstructured_server_id (UUID): ID of the target unstructured data server. To get the ID, run the [Get All
            Unstructured Data Servers](Inventory-Browser#operation/GetAllUnstructuredDataServers) request.
        unstructured_server_name (str | Unset): DNS name of the target unstructured data server.
        error_message (str | Unset): Error message.
    """

    id: UUID
    session_id: UUID
    state: EUnstructuredDataInstantRecoveryMountState
    spec: InstantUnstructuredDataRestoreSpec
    unstructured_server_id: UUID
    unstructured_server_name: str | Unset = UNSET
    error_message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        session_id = str(self.session_id)

        state = self.state.value

        spec = self.spec.to_dict()

        unstructured_server_id = str(self.unstructured_server_id)

        unstructured_server_name = self.unstructured_server_name

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sessionId": session_id,
                "state": state,
                "spec": spec,
                "unstructuredServerId": unstructured_server_id,
            }
        )
        if unstructured_server_name is not UNSET:
            field_dict["unstructuredServerName"] = unstructured_server_name
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.instant_unstructured_data_restore_spec import InstantUnstructuredDataRestoreSpec

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        session_id = UUID(d.pop("sessionId"))

        state = EUnstructuredDataInstantRecoveryMountState(d.pop("state"))

        spec = InstantUnstructuredDataRestoreSpec.from_dict(d.pop("spec"))

        unstructured_server_id = UUID(d.pop("unstructuredServerId"))

        unstructured_server_name = d.pop("unstructuredServerName", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        instant_unstructured_data_recovery_mount = cls(
            id=id,
            session_id=session_id,
            state=state,
            spec=spec,
            unstructured_server_id=unstructured_server_id,
            unstructured_server_name=unstructured_server_name,
            error_message=error_message,
        )

        instant_unstructured_data_recovery_mount.additional_properties = d
        return instant_unstructured_data_recovery_mount

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
