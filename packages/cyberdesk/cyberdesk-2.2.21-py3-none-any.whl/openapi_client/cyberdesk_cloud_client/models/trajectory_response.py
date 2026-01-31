from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trajectory_response_dimensions import TrajectoryResponseDimensions
    from ..models.trajectory_response_original_input_values_type_0 import TrajectoryResponseOriginalInputValuesType0
    from ..models.trajectory_response_trajectory_data_item import TrajectoryResponseTrajectoryDataItem


T = TypeVar("T", bound="TrajectoryResponse")


@_attrs_define
class TrajectoryResponse:
    """Trajectory response schema

    Attributes:
        workflow_id (UUID):
        trajectory_data (list[TrajectoryResponseTrajectoryDataItem]):
        dimensions (TrajectoryResponseDimensions): Display dimensions when trajectory was recorded
        is_approved (bool):
        id (UUID):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        name (None | str | Unset):
        description (None | str | Unset):
        original_input_values (None | TrajectoryResponseOriginalInputValuesType0 | Unset): Original input values used
            when trajectory was created
        user_id (None | Unset | UUID):
        organization_id (None | str | Unset):
    """

    workflow_id: UUID
    trajectory_data: list[TrajectoryResponseTrajectoryDataItem]
    dimensions: TrajectoryResponseDimensions
    is_approved: bool
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    original_input_values: None | TrajectoryResponseOriginalInputValuesType0 | Unset = UNSET
    user_id: None | Unset | UUID = UNSET
    organization_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trajectory_response_original_input_values_type_0 import TrajectoryResponseOriginalInputValuesType0

        workflow_id = str(self.workflow_id)

        trajectory_data = []
        for trajectory_data_item_data in self.trajectory_data:
            trajectory_data_item = trajectory_data_item_data.to_dict()
            trajectory_data.append(trajectory_data_item)

        dimensions = self.dimensions.to_dict()

        is_approved = self.is_approved

        id = str(self.id)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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

        original_input_values: dict[str, Any] | None | Unset
        if isinstance(self.original_input_values, Unset):
            original_input_values = UNSET
        elif isinstance(self.original_input_values, TrajectoryResponseOriginalInputValuesType0):
            original_input_values = self.original_input_values.to_dict()
        else:
            original_input_values = self.original_input_values

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        elif isinstance(self.user_id, UUID):
            user_id = str(self.user_id)
        else:
            user_id = self.user_id

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_id": workflow_id,
                "trajectory_data": trajectory_data,
                "dimensions": dimensions,
                "is_approved": is_approved,
                "id": id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if original_input_values is not UNSET:
            field_dict["original_input_values"] = original_input_values
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trajectory_response_dimensions import TrajectoryResponseDimensions
        from ..models.trajectory_response_original_input_values_type_0 import TrajectoryResponseOriginalInputValuesType0
        from ..models.trajectory_response_trajectory_data_item import TrajectoryResponseTrajectoryDataItem

        d = dict(src_dict)
        workflow_id = UUID(d.pop("workflow_id"))

        trajectory_data = []
        _trajectory_data = d.pop("trajectory_data")
        for trajectory_data_item_data in _trajectory_data:
            trajectory_data_item = TrajectoryResponseTrajectoryDataItem.from_dict(trajectory_data_item_data)

            trajectory_data.append(trajectory_data_item)

        dimensions = TrajectoryResponseDimensions.from_dict(d.pop("dimensions"))

        is_approved = d.pop("is_approved")

        id = UUID(d.pop("id"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

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

        def _parse_original_input_values(data: object) -> None | TrajectoryResponseOriginalInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                original_input_values_type_0 = TrajectoryResponseOriginalInputValuesType0.from_dict(data)

                return original_input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TrajectoryResponseOriginalInputValuesType0 | Unset, data)

        original_input_values = _parse_original_input_values(d.pop("original_input_values", UNSET))

        def _parse_user_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_id_type_0 = UUID(data)

                return user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

        trajectory_response = cls(
            workflow_id=workflow_id,
            trajectory_data=trajectory_data,
            dimensions=dimensions,
            is_approved=is_approved,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            description=description,
            original_input_values=original_input_values,
            user_id=user_id,
            organization_id=organization_id,
        )

        trajectory_response.additional_properties = d
        return trajectory_response

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
