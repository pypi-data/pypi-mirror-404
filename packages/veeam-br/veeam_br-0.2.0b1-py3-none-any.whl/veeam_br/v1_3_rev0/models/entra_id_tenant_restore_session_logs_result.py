from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_restore_session_log_model import EntraIdTenantRestoreSessionLogModel


T = TypeVar("T", bound="EntraIdTenantRestoreSessionLogsResult")


@_attrs_define
class EntraIdTenantRestoreSessionLogsResult:
    """Restore session logs of a Microsoft Entra ID tenant.

    Attributes:
        total_records (int | Unset): Total number of log records.
        records (list[EntraIdTenantRestoreSessionLogModel] | Unset): Array of log records.
    """

    total_records: int | Unset = UNSET
    records: list[EntraIdTenantRestoreSessionLogModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_records = self.total_records

        records: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.records, Unset):
            records = []
            for records_item_data in self.records:
                records_item = records_item_data.to_dict()
                records.append(records_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total_records is not UNSET:
            field_dict["totalRecords"] = total_records
        if records is not UNSET:
            field_dict["records"] = records

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_restore_session_log_model import EntraIdTenantRestoreSessionLogModel

        d = dict(src_dict)
        total_records = d.pop("totalRecords", UNSET)

        _records = d.pop("records", UNSET)
        records: list[EntraIdTenantRestoreSessionLogModel] | Unset = UNSET
        if _records is not UNSET:
            records = []
            for records_item_data in _records:
                records_item = EntraIdTenantRestoreSessionLogModel.from_dict(records_item_data)

                records.append(records_item)

        entra_id_tenant_restore_session_logs_result = cls(
            total_records=total_records,
            records=records,
        )

        entra_id_tenant_restore_session_logs_result.additional_properties = d
        return entra_id_tenant_restore_session_logs_result

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
