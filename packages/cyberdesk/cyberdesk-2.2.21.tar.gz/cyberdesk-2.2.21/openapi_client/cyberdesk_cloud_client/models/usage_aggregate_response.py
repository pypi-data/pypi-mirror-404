from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.usage_mode import UsageMode

T = TypeVar("T", bound="UsageAggregateResponse")


@_attrs_define
class UsageAggregateResponse:
    """Response schema for usage aggregation.

    Attributes:
        total_agentic_steps (int):
        total_cached_steps (int):
        period_start (datetime.datetime):
        period_end (datetime.datetime):
        mode (UsageMode): Mode for counting usage steps.
        runs_counted (int):
    """

    total_agentic_steps: int
    total_cached_steps: int
    period_start: datetime.datetime
    period_end: datetime.datetime
    mode: UsageMode
    runs_counted: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_agentic_steps = self.total_agentic_steps

        total_cached_steps = self.total_cached_steps

        period_start = self.period_start.isoformat()

        period_end = self.period_end.isoformat()

        mode = self.mode.value

        runs_counted = self.runs_counted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_agentic_steps": total_agentic_steps,
                "total_cached_steps": total_cached_steps,
                "period_start": period_start,
                "period_end": period_end,
                "mode": mode,
                "runs_counted": runs_counted,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_agentic_steps = d.pop("total_agentic_steps")

        total_cached_steps = d.pop("total_cached_steps")

        period_start = isoparse(d.pop("period_start"))

        period_end = isoparse(d.pop("period_end"))

        mode = UsageMode(d.pop("mode"))

        runs_counted = d.pop("runs_counted")

        usage_aggregate_response = cls(
            total_agentic_steps=total_agentic_steps,
            total_cached_steps=total_cached_steps,
            period_start=period_start,
            period_end=period_end,
            mode=mode,
            runs_counted=runs_counted,
        )

        usage_aggregate_response.additional_properties = d
        return usage_aggregate_response

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
