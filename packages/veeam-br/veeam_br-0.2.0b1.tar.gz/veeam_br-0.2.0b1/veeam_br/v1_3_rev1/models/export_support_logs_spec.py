from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.export_logs_type import ExportLogsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExportSupportLogsSpec")


@_attrs_define
class ExportSupportLogsSpec:
    """Log collection settings.

    Attributes:
        export_type (ExportLogsType): Log collection scope.
        date_from (datetime.datetime | Unset): Date and time marking the beginning of the period for which you want to
            export logs.
        date_to (datetime.datetime | Unset): Date and time marking the end of the period for which you want to export
            logs.
    """

    export_type: ExportLogsType
    date_from: datetime.datetime | Unset = UNSET
    date_to: datetime.datetime | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        export_type = self.export_type.value

        date_from: str | Unset = UNSET
        if not isinstance(self.date_from, Unset):
            date_from = self.date_from.isoformat()

        date_to: str | Unset = UNSET
        if not isinstance(self.date_to, Unset):
            date_to = self.date_to.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "exportType": export_type,
            }
        )
        if date_from is not UNSET:
            field_dict["dateFrom"] = date_from
        if date_to is not UNSET:
            field_dict["dateTo"] = date_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        export_type = ExportLogsType(d.pop("exportType"))

        _date_from = d.pop("dateFrom", UNSET)
        date_from: datetime.datetime | Unset
        if isinstance(_date_from, Unset):
            date_from = UNSET
        else:
            date_from = isoparse(_date_from)

        _date_to = d.pop("dateTo", UNSET)
        date_to: datetime.datetime | Unset
        if isinstance(_date_to, Unset):
            date_to = UNSET
        else:
            date_to = isoparse(_date_to)

        export_support_logs_spec = cls(
            export_type=export_type,
            date_from=date_from,
            date_to=date_to,
        )

        return export_support_logs_spec
