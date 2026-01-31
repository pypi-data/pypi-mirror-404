from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WorkflowPromptImageResponse")


@_attrs_define
class WorkflowPromptImageResponse:
    """Response schema for uploaded workflow prompt image

    Attributes:
        supabase_url (str): The stable supabase:// URL to use in workflow prompt HTML. Example: supabase://workflow-
            prompt-images/org_xxx/prompt-assets/image.png
        signed_url (str): A temporary signed URL for immediate display (expires in 1 hour)
        filename (str): The sanitized filename as stored
        content_type (str): The MIME type of the uploaded image
        size_bytes (int): The size of the uploaded file in bytes
    """

    supabase_url: str
    signed_url: str
    filename: str
    content_type: str
    size_bytes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        supabase_url = self.supabase_url

        signed_url = self.signed_url

        filename = self.filename

        content_type = self.content_type

        size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "supabase_url": supabase_url,
                "signed_url": signed_url,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        supabase_url = d.pop("supabase_url")

        signed_url = d.pop("signed_url")

        filename = d.pop("filename")

        content_type = d.pop("content_type")

        size_bytes = d.pop("size_bytes")

        workflow_prompt_image_response = cls(
            supabase_url=supabase_url,
            signed_url=signed_url,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )

        workflow_prompt_image_response.additional_properties = d
        return workflow_prompt_image_response

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
