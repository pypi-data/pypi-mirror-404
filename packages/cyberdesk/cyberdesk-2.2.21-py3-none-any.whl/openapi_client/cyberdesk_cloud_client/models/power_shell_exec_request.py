from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PowerShellExecRequest")


@_attrs_define
class PowerShellExecRequest:
    """
    Attributes:
        command (str): PowerShell command to execute
        same_session (bool | Unset): Use persistent session Default: True.
        working_directory (None | str | Unset): Working directory for new session
        session_id (None | str | Unset): Session ID to use
        timeout (float | None | Unset): Maximum time in seconds to wait for command completion before continuing. The
            command will continue running in the background after timeout (default: 30.0) Default: 30.0.
    """

    command: str
    same_session: bool | Unset = True
    working_directory: None | str | Unset = UNSET
    session_id: None | str | Unset = UNSET
    timeout: float | None | Unset = 30.0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        command = self.command

        same_session = self.same_session

        working_directory: None | str | Unset
        if isinstance(self.working_directory, Unset):
            working_directory = UNSET
        else:
            working_directory = self.working_directory

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        else:
            session_id = self.session_id

        timeout: float | None | Unset
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "command": command,
            }
        )
        if same_session is not UNSET:
            field_dict["same_session"] = same_session
        if working_directory is not UNSET:
            field_dict["working_directory"] = working_directory
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if timeout is not UNSET:
            field_dict["timeout"] = timeout

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        command = d.pop("command")

        same_session = d.pop("same_session", UNSET)

        def _parse_working_directory(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        working_directory = _parse_working_directory(d.pop("working_directory", UNSET))

        def _parse_session_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        def _parse_timeout(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        power_shell_exec_request = cls(
            command=command,
            same_session=same_session,
            working_directory=working_directory,
            session_id=session_id,
            timeout=timeout,
        )

        power_shell_exec_request.additional_properties = d
        return power_shell_exec_request

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
