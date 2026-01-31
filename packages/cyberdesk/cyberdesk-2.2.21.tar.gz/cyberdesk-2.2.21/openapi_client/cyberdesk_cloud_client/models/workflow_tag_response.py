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
    from ..models.workflow_tag_group_response import WorkflowTagGroupResponse


T = TypeVar("T", bound="WorkflowTagResponse")


@_attrs_define
class WorkflowTagResponse:
    """Workflow tag response schema

    Attributes:
        name (str):
        id (UUID):
        organization_id (str):
        order (int):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        emoji (None | str | Unset):
        color (None | str | Unset):
        group_id (None | Unset | UUID): Optional group for mutual exclusivity
        is_archived (bool | Unset):  Default: False.
        workflow_count (int | None | Unset): Number of workflows with this tag (returned in list endpoint)
        group (None | Unset | WorkflowTagGroupResponse): The group this tag belongs to
    """

    name: str
    id: UUID
    organization_id: str
    order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    emoji: None | str | Unset = UNSET
    color: None | str | Unset = UNSET
    group_id: None | Unset | UUID = UNSET
    is_archived: bool | Unset = False
    workflow_count: int | None | Unset = UNSET
    group: None | Unset | WorkflowTagGroupResponse = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.workflow_tag_group_response import WorkflowTagGroupResponse

        name = self.name

        id = str(self.id)

        organization_id = self.organization_id

        order = self.order

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        emoji: None | str | Unset
        if isinstance(self.emoji, Unset):
            emoji = UNSET
        else:
            emoji = self.emoji

        color: None | str | Unset
        if isinstance(self.color, Unset):
            color = UNSET
        else:
            color = self.color

        group_id: None | str | Unset
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        elif isinstance(self.group_id, UUID):
            group_id = str(self.group_id)
        else:
            group_id = self.group_id

        is_archived = self.is_archived

        workflow_count: int | None | Unset
        if isinstance(self.workflow_count, Unset):
            workflow_count = UNSET
        else:
            workflow_count = self.workflow_count

        group: dict[str, Any] | None | Unset
        if isinstance(self.group, Unset):
            group = UNSET
        elif isinstance(self.group, WorkflowTagGroupResponse):
            group = self.group.to_dict()
        else:
            group = self.group

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "organization_id": organization_id,
                "order": order,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if emoji is not UNSET:
            field_dict["emoji"] = emoji
        if color is not UNSET:
            field_dict["color"] = color
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if is_archived is not UNSET:
            field_dict["is_archived"] = is_archived
        if workflow_count is not UNSET:
            field_dict["workflow_count"] = workflow_count
        if group is not UNSET:
            field_dict["group"] = group

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workflow_tag_group_response import WorkflowTagGroupResponse

        d = dict(src_dict)
        name = d.pop("name")

        id = UUID(d.pop("id"))

        organization_id = d.pop("organization_id")

        order = d.pop("order")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_emoji(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        emoji = _parse_emoji(d.pop("emoji", UNSET))

        def _parse_color(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        color = _parse_color(d.pop("color", UNSET))

        def _parse_group_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                group_id_type_0 = UUID(data)

                return group_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        group_id = _parse_group_id(d.pop("group_id", UNSET))

        is_archived = d.pop("is_archived", UNSET)

        def _parse_workflow_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        workflow_count = _parse_workflow_count(d.pop("workflow_count", UNSET))

        def _parse_group(data: object) -> None | Unset | WorkflowTagGroupResponse:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                group_type_0 = WorkflowTagGroupResponse.from_dict(data)

                return group_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WorkflowTagGroupResponse, data)

        group = _parse_group(d.pop("group", UNSET))

        workflow_tag_response = cls(
            name=name,
            id=id,
            organization_id=organization_id,
            order=order,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            emoji=emoji,
            color=color,
            group_id=group_id,
            is_archived=is_archived,
            workflow_count=workflow_count,
            group=group,
        )

        workflow_tag_response.additional_properties = d
        return workflow_tag_response

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
