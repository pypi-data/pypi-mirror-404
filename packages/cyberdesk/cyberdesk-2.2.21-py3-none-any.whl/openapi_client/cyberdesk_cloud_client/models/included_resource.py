from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="IncludedResource")


@_attrs_define
class IncludedResource:
    """A resource in the JSON:API-style included array.

    Each included resource has a `type` field indicating what kind of resource it is
    (e.g., "workflow", "machine", "pool") and an `id` field with the resource's UUID.
    All other fields from the resource's response model are included.

    Example:
        {
            "type": "workflow",
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "My Workflow",
            "main_prompt": "Do something...",
            "created_at": "2024-01-15T10:30:00Z"
        }

        Attributes:
            type_ (str): Resource type (e.g., 'workflow', 'machine', 'pool')
            id (UUID): Resource UUID
    """

    type_: str
    id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        id = str(self.id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = d.pop("type")

        id = UUID(d.pop("id"))

        included_resource = cls(
            type_=type_,
            id=id,
        )

        included_resource.additional_properties = d
        return included_resource

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
