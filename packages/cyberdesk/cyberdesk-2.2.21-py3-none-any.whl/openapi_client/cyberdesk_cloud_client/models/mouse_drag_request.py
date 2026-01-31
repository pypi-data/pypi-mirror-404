from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MouseDragRequest")


@_attrs_define
class MouseDragRequest:
    """
    Attributes:
        to_x (int):
        to_y (int):
        start_x (int):
        start_y (int):
        duration (float | None | Unset):
        button (None | str | Unset): 'left' | 'right' | 'middle' Default: 'left'.
    """

    to_x: int
    to_y: int
    start_x: int
    start_y: int
    duration: float | None | Unset = UNSET
    button: None | str | Unset = "left"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        to_x = self.to_x

        to_y = self.to_y

        start_x = self.start_x

        start_y = self.start_y

        duration: float | None | Unset
        if isinstance(self.duration, Unset):
            duration = UNSET
        else:
            duration = self.duration

        button: None | str | Unset
        if isinstance(self.button, Unset):
            button = UNSET
        else:
            button = self.button

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "to_x": to_x,
                "to_y": to_y,
                "start_x": start_x,
                "start_y": start_y,
            }
        )
        if duration is not UNSET:
            field_dict["duration"] = duration
        if button is not UNSET:
            field_dict["button"] = button

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        to_x = d.pop("to_x")

        to_y = d.pop("to_y")

        start_x = d.pop("start_x")

        start_y = d.pop("start_y")

        def _parse_duration(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        duration = _parse_duration(d.pop("duration", UNSET))

        def _parse_button(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        button = _parse_button(d.pop("button", UNSET))

        mouse_drag_request = cls(
            to_x=to_x,
            to_y=to_y,
            start_x=start_x,
            start_y=start_y,
            duration=duration,
            button=button,
        )

        mouse_drag_request.additional_properties = d
        return mouse_drag_request

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
