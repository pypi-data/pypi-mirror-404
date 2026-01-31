from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BulkAddTagsRequest")


@_attrs_define
class BulkAddTagsRequest:
    """Schema for bulk adding tags to workflows

    Attributes:
        workflow_ids (list[UUID]): List of workflow IDs to add tags to
        tag_ids (list[UUID]): List of tag IDs to add
    """

    workflow_ids: list[UUID]
    tag_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_ids = []
        for workflow_ids_item_data in self.workflow_ids:
            workflow_ids_item = str(workflow_ids_item_data)
            workflow_ids.append(workflow_ids_item)

        tag_ids = []
        for tag_ids_item_data in self.tag_ids:
            tag_ids_item = str(tag_ids_item_data)
            tag_ids.append(tag_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_ids": workflow_ids,
                "tag_ids": tag_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workflow_ids = []
        _workflow_ids = d.pop("workflow_ids")
        for workflow_ids_item_data in _workflow_ids:
            workflow_ids_item = UUID(workflow_ids_item_data)

            workflow_ids.append(workflow_ids_item)

        tag_ids = []
        _tag_ids = d.pop("tag_ids")
        for tag_ids_item_data in _tag_ids:
            tag_ids_item = UUID(tag_ids_item_data)

            tag_ids.append(tag_ids_item)

        bulk_add_tags_request = cls(
            workflow_ids=workflow_ids,
            tag_ids=tag_ids,
        )

        bulk_add_tags_request.additional_properties = d
        return bulk_add_tags_request

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
