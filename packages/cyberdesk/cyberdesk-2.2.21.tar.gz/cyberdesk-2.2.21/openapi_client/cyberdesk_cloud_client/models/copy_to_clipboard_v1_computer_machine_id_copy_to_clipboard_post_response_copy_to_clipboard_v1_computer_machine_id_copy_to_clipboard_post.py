from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar(
    "T",
    bound="CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost",
)


@_attrs_define
class CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost:
    """ """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post_response_copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post = cls()

        copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post_response_copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post.additional_properties = d
        return copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post_response_copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post

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
