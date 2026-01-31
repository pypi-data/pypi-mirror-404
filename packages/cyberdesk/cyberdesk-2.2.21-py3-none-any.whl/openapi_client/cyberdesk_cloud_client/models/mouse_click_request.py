from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MouseClickRequest")


@_attrs_define
class MouseClickRequest:
    """
    Attributes:
        x (int | None | Unset):
        y (int | None | Unset):
        button (str | Unset):  Default: 'left'.
        down (bool | None | Unset): None = full click, True = mouse down, False = mouse up
        clicks (int | Unset): Number of clicks (1=single, 2=double, 3=triple) Default: 1.
    """

    x: int | None | Unset = UNSET
    y: int | None | Unset = UNSET
    button: str | Unset = "left"
    down: bool | None | Unset = UNSET
    clicks: int | Unset = 1
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        x: int | None | Unset
        if isinstance(self.x, Unset):
            x = UNSET
        else:
            x = self.x

        y: int | None | Unset
        if isinstance(self.y, Unset):
            y = UNSET
        else:
            y = self.y

        button = self.button

        down: bool | None | Unset
        if isinstance(self.down, Unset):
            down = UNSET
        else:
            down = self.down

        clicks = self.clicks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if x is not UNSET:
            field_dict["x"] = x
        if y is not UNSET:
            field_dict["y"] = y
        if button is not UNSET:
            field_dict["button"] = button
        if down is not UNSET:
            field_dict["down"] = down
        if clicks is not UNSET:
            field_dict["clicks"] = clicks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_x(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        x = _parse_x(d.pop("x", UNSET))

        def _parse_y(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        y = _parse_y(d.pop("y", UNSET))

        button = d.pop("button", UNSET)

        def _parse_down(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        down = _parse_down(d.pop("down", UNSET))

        clicks = d.pop("clicks", UNSET)

        mouse_click_request = cls(
            x=x,
            y=y,
            button=button,
            down=down,
            clicks=clicks,
        )

        mouse_click_request.additional_properties = d
        return mouse_click_request

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
