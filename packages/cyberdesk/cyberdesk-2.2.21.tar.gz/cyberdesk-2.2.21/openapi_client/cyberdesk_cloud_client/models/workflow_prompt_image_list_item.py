from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkflowPromptImageListItem")


@_attrs_define
class WorkflowPromptImageListItem:
    """Schema for an item in the workflow prompt images list

    Attributes:
        supabase_url (str): The stable supabase:// URL to use in workflow prompt HTML
        path (str): The storage path of the image
        filename (str): The filename of the image
        created_at (datetime.datetime | None | Unset): When the image was uploaded
        size_bytes (int | None | Unset): The size of the file in bytes
    """

    supabase_url: str
    path: str
    filename: str
    created_at: datetime.datetime | None | Unset = UNSET
    size_bytes: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        supabase_url = self.supabase_url

        path = self.path

        filename = self.filename

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "supabase_url": supabase_url,
                "path": path,
                "filename": filename,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        supabase_url = d.pop("supabase_url")

        path = d.pop("path")

        filename = d.pop("filename")

        def _parse_created_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes", UNSET))

        workflow_prompt_image_list_item = cls(
            supabase_url=supabase_url,
            path=path,
            filename=filename,
            created_at=created_at,
            size_bytes=size_bytes,
        )

        workflow_prompt_image_list_item.additional_properties = d
        return workflow_prompt_image_list_item

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
