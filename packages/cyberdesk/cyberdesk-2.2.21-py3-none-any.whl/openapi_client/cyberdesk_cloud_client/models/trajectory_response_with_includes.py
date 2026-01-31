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
    from ..models.included_resource import IncludedResource
    from ..models.trajectory_response_with_includes_dimensions import TrajectoryResponseWithIncludesDimensions
    from ..models.trajectory_response_with_includes_original_input_values_type_0 import (
        TrajectoryResponseWithIncludesOriginalInputValuesType0,
    )
    from ..models.trajectory_response_with_includes_trajectory_data_type_0_item import (
        TrajectoryResponseWithIncludesTrajectoryDataType0Item,
    )


T = TypeVar("T", bound="TrajectoryResponseWithIncludes")


@_attrs_define
class TrajectoryResponseWithIncludes:
    """Trajectory response with optional included related resources.

    Attributes:
        id (UUID):
        workflow_id (UUID):
        is_approved (bool):
        dimensions (TrajectoryResponseWithIncludesDimensions): Display dimensions when trajectory was recorded
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        user_id (None | Unset | UUID):
        organization_id (None | str | Unset):
        name (None | str | Unset):
        description (None | str | Unset):
        trajectory_data (list[TrajectoryResponseWithIncludesTrajectoryDataType0Item] | None | Unset):
        original_input_values (None | TrajectoryResponseWithIncludesOriginalInputValuesType0 | Unset): Original input
            values used when trajectory was created
        included (list[IncludedResource] | None | Unset): Related resources requested via the `include` query parameter
    """

    id: UUID
    workflow_id: UUID
    is_approved: bool
    dimensions: TrajectoryResponseWithIncludesDimensions
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user_id: None | Unset | UUID = UNSET
    organization_id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    trajectory_data: list[TrajectoryResponseWithIncludesTrajectoryDataType0Item] | None | Unset = UNSET
    original_input_values: None | TrajectoryResponseWithIncludesOriginalInputValuesType0 | Unset = UNSET
    included: list[IncludedResource] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trajectory_response_with_includes_original_input_values_type_0 import (
            TrajectoryResponseWithIncludesOriginalInputValuesType0,
        )

        id = str(self.id)

        workflow_id = str(self.workflow_id)

        is_approved = self.is_approved

        dimensions = self.dimensions.to_dict()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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

        original_input_values: dict[str, Any] | None | Unset
        if isinstance(self.original_input_values, Unset):
            original_input_values = UNSET
        elif isinstance(self.original_input_values, TrajectoryResponseWithIncludesOriginalInputValuesType0):
            original_input_values = self.original_input_values.to_dict()
        else:
            original_input_values = self.original_input_values

        included: list[dict[str, Any]] | None | Unset
        if isinstance(self.included, Unset):
            included = UNSET
        elif isinstance(self.included, list):
            included = []
            for included_type_0_item_data in self.included:
                included_type_0_item = included_type_0_item_data.to_dict()
                included.append(included_type_0_item)

        else:
            included = self.included

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "workflow_id": workflow_id,
                "is_approved": is_approved,
                "dimensions": dimensions,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if trajectory_data is not UNSET:
            field_dict["trajectory_data"] = trajectory_data
        if original_input_values is not UNSET:
            field_dict["original_input_values"] = original_input_values
        if included is not UNSET:
            field_dict["included"] = included

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.included_resource import IncludedResource
        from ..models.trajectory_response_with_includes_dimensions import TrajectoryResponseWithIncludesDimensions
        from ..models.trajectory_response_with_includes_original_input_values_type_0 import (
            TrajectoryResponseWithIncludesOriginalInputValuesType0,
        )
        from ..models.trajectory_response_with_includes_trajectory_data_type_0_item import (
            TrajectoryResponseWithIncludesTrajectoryDataType0Item,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        workflow_id = UUID(d.pop("workflow_id"))

        is_approved = d.pop("is_approved")

        dimensions = TrajectoryResponseWithIncludesDimensions.from_dict(d.pop("dimensions"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

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

        def _parse_trajectory_data(
            data: object,
        ) -> list[TrajectoryResponseWithIncludesTrajectoryDataType0Item] | None | Unset:
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
                    trajectory_data_type_0_item = TrajectoryResponseWithIncludesTrajectoryDataType0Item.from_dict(
                        trajectory_data_type_0_item_data
                    )

                    trajectory_data_type_0.append(trajectory_data_type_0_item)

                return trajectory_data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[TrajectoryResponseWithIncludesTrajectoryDataType0Item] | None | Unset, data)

        trajectory_data = _parse_trajectory_data(d.pop("trajectory_data", UNSET))

        def _parse_original_input_values(
            data: object,
        ) -> None | TrajectoryResponseWithIncludesOriginalInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                original_input_values_type_0 = TrajectoryResponseWithIncludesOriginalInputValuesType0.from_dict(data)

                return original_input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TrajectoryResponseWithIncludesOriginalInputValuesType0 | Unset, data)

        original_input_values = _parse_original_input_values(d.pop("original_input_values", UNSET))

        def _parse_included(data: object) -> list[IncludedResource] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                included_type_0 = []
                _included_type_0 = data
                for included_type_0_item_data in _included_type_0:
                    included_type_0_item = IncludedResource.from_dict(included_type_0_item_data)

                    included_type_0.append(included_type_0_item)

                return included_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[IncludedResource] | None | Unset, data)

        included = _parse_included(d.pop("included", UNSET))

        trajectory_response_with_includes = cls(
            id=id,
            workflow_id=workflow_id,
            is_approved=is_approved,
            dimensions=dimensions,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            organization_id=organization_id,
            name=name,
            description=description,
            trajectory_data=trajectory_data,
            original_input_values=original_input_values,
            included=included,
        )

        trajectory_response_with_includes.additional_properties = d
        return trajectory_response_with_includes

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
