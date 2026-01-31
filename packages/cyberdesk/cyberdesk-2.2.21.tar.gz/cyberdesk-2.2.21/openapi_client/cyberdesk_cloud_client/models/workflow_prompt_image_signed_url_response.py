from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WorkflowPromptImageSignedUrlResponse")


@_attrs_define
class WorkflowPromptImageSignedUrlResponse:
    """Response schema for getting a signed URL for an existing image

    Attributes:
        supabase_url (str): The stable supabase:// URL
        signed_url (str): A temporary signed URL (expires in 1 hour)
        expires_in (int): Seconds until the signed URL expires
    """

    supabase_url: str
    signed_url: str
    expires_in: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        supabase_url = self.supabase_url

        signed_url = self.signed_url

        expires_in = self.expires_in

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "supabase_url": supabase_url,
                "signed_url": signed_url,
                "expires_in": expires_in,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        supabase_url = d.pop("supabase_url")

        signed_url = d.pop("signed_url")

        expires_in = d.pop("expires_in")

        workflow_prompt_image_signed_url_response = cls(
            supabase_url=supabase_url,
            signed_url=signed_url,
            expires_in=expires_in,
        )

        workflow_prompt_image_signed_url_response.additional_properties = d
        return workflow_prompt_image_signed_url_response

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
