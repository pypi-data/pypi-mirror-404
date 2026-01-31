from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_session_bottleneck_type import ESessionBottleneckType

T = TypeVar("T", bound="SessionProgressType0")


@_attrs_define
class SessionProgressType0:
    """Details on the progress of the session.

    Attributes:
        duration (str): Time from the session start till the current moment or job end.
        processing_rate (None | str): Average speed of data processing.
        bottleneck (ESessionBottleneckType): Session bottleneck type.
        processed_size (int | None): Total size of all disks processed in the session.
        read_size (int | None): Amount of data read from the datastore by the source-side Data Mover prior to applying
            compression and deduplication.
        transferred_size (int | None): Amount of data transferred from the source-side Veeam Data Mover to the target-
            side Veeam Data Mover after applying compression and deduplication.
    """

    duration: str
    processing_rate: None | str
    bottleneck: ESessionBottleneckType
    processed_size: int | None
    read_size: int | None
    transferred_size: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        duration = self.duration

        processing_rate: None | str
        processing_rate = self.processing_rate

        bottleneck = self.bottleneck.value

        processed_size: int | None
        processed_size = self.processed_size

        read_size: int | None
        read_size = self.read_size

        transferred_size: int | None
        transferred_size = self.transferred_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "duration": duration,
                "processingRate": processing_rate,
                "bottleneck": bottleneck,
                "processedSize": processed_size,
                "readSize": read_size,
                "transferredSize": transferred_size,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        duration = d.pop("duration")

        def _parse_processing_rate(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        processing_rate = _parse_processing_rate(d.pop("processingRate"))

        bottleneck = ESessionBottleneckType(d.pop("bottleneck"))

        def _parse_processed_size(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        processed_size = _parse_processed_size(d.pop("processedSize"))

        def _parse_read_size(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        read_size = _parse_read_size(d.pop("readSize"))

        def _parse_transferred_size(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        transferred_size = _parse_transferred_size(d.pop("transferredSize"))

        session_progress_type_0 = cls(
            duration=duration,
            processing_rate=processing_rate,
            bottleneck=bottleneck,
            processed_size=processed_size,
            read_size=read_size,
            transferred_size=transferred_size,
        )

        session_progress_type_0.additional_properties = d
        return session_progress_type_0

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
