from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestLogResponse")


@_attrs_define
class RequestLogResponse:
    """Request log response schema

    Attributes:
        request_id (str):
        method (str):
        path (str):
        id (UUID):
        machine_id (UUID):
        created_at (datetime.datetime):
        completed_at (datetime.datetime | None):
        status_code (int | None | Unset):
        request_size_bytes (int | None | Unset):
        response_size_bytes (int | None | Unset):
        duration_ms (int | None | Unset):
        error_message (None | str | Unset):
        organization_id (None | str | Unset):
    """

    request_id: str
    method: str
    path: str
    id: UUID
    machine_id: UUID
    created_at: datetime.datetime
    completed_at: datetime.datetime | None
    status_code: int | None | Unset = UNSET
    request_size_bytes: int | None | Unset = UNSET
    response_size_bytes: int | None | Unset = UNSET
    duration_ms: int | None | Unset = UNSET
    error_message: None | str | Unset = UNSET
    organization_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        request_id = self.request_id

        method = self.method

        path = self.path

        id = str(self.id)

        machine_id = str(self.machine_id)

        created_at = self.created_at.isoformat()

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        status_code: int | None | Unset
        if isinstance(self.status_code, Unset):
            status_code = UNSET
        else:
            status_code = self.status_code

        request_size_bytes: int | None | Unset
        if isinstance(self.request_size_bytes, Unset):
            request_size_bytes = UNSET
        else:
            request_size_bytes = self.request_size_bytes

        response_size_bytes: int | None | Unset
        if isinstance(self.response_size_bytes, Unset):
            response_size_bytes = UNSET
        else:
            response_size_bytes = self.response_size_bytes

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "request_id": request_id,
                "method": method,
                "path": path,
                "id": id,
                "machine_id": machine_id,
                "created_at": created_at,
                "completed_at": completed_at,
            }
        )
        if status_code is not UNSET:
            field_dict["status_code"] = status_code
        if request_size_bytes is not UNSET:
            field_dict["request_size_bytes"] = request_size_bytes
        if response_size_bytes is not UNSET:
            field_dict["response_size_bytes"] = response_size_bytes
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if error_message is not UNSET:
            field_dict["error_message"] = error_message
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        request_id = d.pop("request_id")

        method = d.pop("method")

        path = d.pop("path")

        id = UUID(d.pop("id"))

        machine_id = UUID(d.pop("machine_id"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_completed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        completed_at = _parse_completed_at(d.pop("completed_at"))

        def _parse_status_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        status_code = _parse_status_code(d.pop("status_code", UNSET))

        def _parse_request_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        request_size_bytes = _parse_request_size_bytes(d.pop("request_size_bytes", UNSET))

        def _parse_response_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        response_size_bytes = _parse_response_size_bytes(d.pop("response_size_bytes", UNSET))

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

        request_log_response = cls(
            request_id=request_id,
            method=method,
            path=path,
            id=id,
            machine_id=machine_id,
            created_at=created_at,
            completed_at=completed_at,
            status_code=status_code,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            duration_ms=duration_ms,
            error_message=error_message,
            organization_id=organization_id,
        )

        request_log_response.additional_properties = d
        return request_log_response

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
