from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.run_status import RunStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_update_input_values_type_0 import RunUpdateInputValuesType0
    from ..models.run_update_output_data_type_0 import RunUpdateOutputDataType0
    from ..models.run_update_run_message_history_type_0_item import RunUpdateRunMessageHistoryType0Item
    from ..models.run_update_usage_metadata_type_0 import RunUpdateUsageMetadataType0


T = TypeVar("T", bound="RunUpdate")


@_attrs_define
class RunUpdate:
    """Schema for updating a run

    Attributes:
        status (None | RunStatus | Unset):
        error (list[str] | None | Unset):
        output_data (None | RunUpdateOutputDataType0 | Unset):
        output_attachment_ids (list[str] | None | Unset):
        run_message_history (list[RunUpdateRunMessageHistoryType0Item] | None | Unset):
        input_values (None | RunUpdateInputValuesType0 | Unset):
        usage_metadata (None | RunUpdateUsageMetadataType0 | Unset):
        started_at (datetime.datetime | None | Unset):
        ended_at (datetime.datetime | None | Unset):
        release_session_after (bool | None | Unset):
    """

    status: None | RunStatus | Unset = UNSET
    error: list[str] | None | Unset = UNSET
    output_data: None | RunUpdateOutputDataType0 | Unset = UNSET
    output_attachment_ids: list[str] | None | Unset = UNSET
    run_message_history: list[RunUpdateRunMessageHistoryType0Item] | None | Unset = UNSET
    input_values: None | RunUpdateInputValuesType0 | Unset = UNSET
    usage_metadata: None | RunUpdateUsageMetadataType0 | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    release_session_after: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_update_input_values_type_0 import RunUpdateInputValuesType0
        from ..models.run_update_output_data_type_0 import RunUpdateOutputDataType0
        from ..models.run_update_usage_metadata_type_0 import RunUpdateUsageMetadataType0

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, RunStatus):
            status = self.status.value
        else:
            status = self.status

        error: list[str] | None | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, list):
            error = self.error

        else:
            error = self.error

        output_data: dict[str, Any] | None | Unset
        if isinstance(self.output_data, Unset):
            output_data = UNSET
        elif isinstance(self.output_data, RunUpdateOutputDataType0):
            output_data = self.output_data.to_dict()
        else:
            output_data = self.output_data

        output_attachment_ids: list[str] | None | Unset
        if isinstance(self.output_attachment_ids, Unset):
            output_attachment_ids = UNSET
        elif isinstance(self.output_attachment_ids, list):
            output_attachment_ids = self.output_attachment_ids

        else:
            output_attachment_ids = self.output_attachment_ids

        run_message_history: list[dict[str, Any]] | None | Unset
        if isinstance(self.run_message_history, Unset):
            run_message_history = UNSET
        elif isinstance(self.run_message_history, list):
            run_message_history = []
            for run_message_history_type_0_item_data in self.run_message_history:
                run_message_history_type_0_item = run_message_history_type_0_item_data.to_dict()
                run_message_history.append(run_message_history_type_0_item)

        else:
            run_message_history = self.run_message_history

        input_values: dict[str, Any] | None | Unset
        if isinstance(self.input_values, Unset):
            input_values = UNSET
        elif isinstance(self.input_values, RunUpdateInputValuesType0):
            input_values = self.input_values.to_dict()
        else:
            input_values = self.input_values

        usage_metadata: dict[str, Any] | None | Unset
        if isinstance(self.usage_metadata, Unset):
            usage_metadata = UNSET
        elif isinstance(self.usage_metadata, RunUpdateUsageMetadataType0):
            usage_metadata = self.usage_metadata.to_dict()
        else:
            usage_metadata = self.usage_metadata

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        release_session_after: bool | None | Unset
        if isinstance(self.release_session_after, Unset):
            release_session_after = UNSET
        else:
            release_session_after = self.release_session_after

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if error is not UNSET:
            field_dict["error"] = error
        if output_data is not UNSET:
            field_dict["output_data"] = output_data
        if output_attachment_ids is not UNSET:
            field_dict["output_attachment_ids"] = output_attachment_ids
        if run_message_history is not UNSET:
            field_dict["run_message_history"] = run_message_history
        if input_values is not UNSET:
            field_dict["input_values"] = input_values
        if usage_metadata is not UNSET:
            field_dict["usage_metadata"] = usage_metadata
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if release_session_after is not UNSET:
            field_dict["release_session_after"] = release_session_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_update_input_values_type_0 import RunUpdateInputValuesType0
        from ..models.run_update_output_data_type_0 import RunUpdateOutputDataType0
        from ..models.run_update_run_message_history_type_0_item import RunUpdateRunMessageHistoryType0Item
        from ..models.run_update_usage_metadata_type_0 import RunUpdateUsageMetadataType0

        d = dict(src_dict)

        def _parse_status(data: object) -> None | RunStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = RunStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunStatus | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_error(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                error_type_0 = cast(list[str], data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_output_data(data: object) -> None | RunUpdateOutputDataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_data_type_0 = RunUpdateOutputDataType0.from_dict(data)

                return output_data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunUpdateOutputDataType0 | Unset, data)

        output_data = _parse_output_data(d.pop("output_data", UNSET))

        def _parse_output_attachment_ids(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                output_attachment_ids_type_0 = cast(list[str], data)

                return output_attachment_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        output_attachment_ids = _parse_output_attachment_ids(d.pop("output_attachment_ids", UNSET))

        def _parse_run_message_history(data: object) -> list[RunUpdateRunMessageHistoryType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                run_message_history_type_0 = []
                _run_message_history_type_0 = data
                for run_message_history_type_0_item_data in _run_message_history_type_0:
                    run_message_history_type_0_item = RunUpdateRunMessageHistoryType0Item.from_dict(
                        run_message_history_type_0_item_data
                    )

                    run_message_history_type_0.append(run_message_history_type_0_item)

                return run_message_history_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[RunUpdateRunMessageHistoryType0Item] | None | Unset, data)

        run_message_history = _parse_run_message_history(d.pop("run_message_history", UNSET))

        def _parse_input_values(data: object) -> None | RunUpdateInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_values_type_0 = RunUpdateInputValuesType0.from_dict(data)

                return input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunUpdateInputValuesType0 | Unset, data)

        input_values = _parse_input_values(d.pop("input_values", UNSET))

        def _parse_usage_metadata(data: object) -> None | RunUpdateUsageMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                usage_metadata_type_0 = RunUpdateUsageMetadataType0.from_dict(data)

                return usage_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunUpdateUsageMetadataType0 | Unset, data)

        usage_metadata = _parse_usage_metadata(d.pop("usage_metadata", UNSET))

        def _parse_started_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        def _parse_release_session_after(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        release_session_after = _parse_release_session_after(d.pop("release_session_after", UNSET))

        run_update = cls(
            status=status,
            error=error,
            output_data=output_data,
            output_attachment_ids=output_attachment_ids,
            run_message_history=run_message_history,
            input_values=input_values,
            usage_metadata=usage_metadata,
            started_at=started_at,
            ended_at=ended_at,
            release_session_after=release_session_after,
        )

        run_update.additional_properties = d
        return run_update

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
