from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trajectory_update_trajectory_data_type_0_item import TrajectoryUpdateTrajectoryDataType0Item


T = TypeVar("T", bound="TrajectoryUpdate")


@_attrs_define
class TrajectoryUpdate:
    """Schema for updating a trajectory

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        trajectory_data (list[TrajectoryUpdateTrajectoryDataType0Item] | None | Unset):
        is_approved (bool | None | Unset): Whether this trajectory is approved for use
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    trajectory_data: list[TrajectoryUpdateTrajectoryDataType0Item] | None | Unset = UNSET
    is_approved: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        trajectory_data: list[dict[str, Any]] | None | Unset
        if isinstance(self.trajectory_data, Unset):
            trajectory_data = UNSET
        elif isinstance(self.trajectory_data, list):
            trajectory_data = []
            for trajectory_data_type_0_item_data in self.trajectory_data:
                trajectory_data_type_0_item = trajectory_data_type_0_item_data.to_dict()
                trajectory_data.append(trajectory_data_type_0_item)

        else:
            trajectory_data = self.trajectory_data

        is_approved: bool | None | Unset
        if isinstance(self.is_approved, Unset):
            is_approved = UNSET
        else:
            is_approved = self.is_approved

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if trajectory_data is not UNSET:
            field_dict["trajectory_data"] = trajectory_data
        if is_approved is not UNSET:
            field_dict["is_approved"] = is_approved

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trajectory_update_trajectory_data_type_0_item import TrajectoryUpdateTrajectoryDataType0Item

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_trajectory_data(data: object) -> list[TrajectoryUpdateTrajectoryDataType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                trajectory_data_type_0 = []
                _trajectory_data_type_0 = data
                for trajectory_data_type_0_item_data in _trajectory_data_type_0:
                    trajectory_data_type_0_item = TrajectoryUpdateTrajectoryDataType0Item.from_dict(
                        trajectory_data_type_0_item_data
                    )

                    trajectory_data_type_0.append(trajectory_data_type_0_item)

                return trajectory_data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[TrajectoryUpdateTrajectoryDataType0Item] | None | Unset, data)

        trajectory_data = _parse_trajectory_data(d.pop("trajectory_data", UNSET))

        def _parse_is_approved(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_approved = _parse_is_approved(d.pop("is_approved", UNSET))

        trajectory_update = cls(
            name=name,
            description=description,
            trajectory_data=trajectory_data,
            is_approved=is_approved,
        )

        trajectory_update.additional_properties = d
        return trajectory_update

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
