from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.run_status import RunStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_response_input_values_type_0 import RunResponseInputValuesType0
    from ..models.run_response_output_data_type_0 import RunResponseOutputDataType0
    from ..models.run_response_run_message_history_type_0_item import RunResponseRunMessageHistoryType0Item
    from ..models.run_response_sensitive_input_aliases_type_0 import RunResponseSensitiveInputAliasesType0
    from ..models.run_response_usage_metadata_type_0 import RunResponseUsageMetadataType0


T = TypeVar("T", bound="RunResponse")


@_attrs_define
class RunResponse:
    """Run response schema

    Attributes:
        workflow_id (UUID):
        machine_id (None | UUID):
        id (UUID):
        status (RunStatus):
        created_at (datetime.datetime):
        user_id (None | Unset | UUID):
        organization_id (None | str | Unset):
        error (list[str] | None | Unset):
        output_data (None | RunResponseOutputDataType0 | Unset):
        input_attachment_ids (list[str] | None | Unset):
        output_attachment_ids (list[str] | None | Unset):
        run_message_history (list[RunResponseRunMessageHistoryType0Item] | None | Unset):
        input_values (None | RunResponseInputValuesType0 | Unset):
        pool_ids (list[UUID] | None | Unset):
        sensitive_input_aliases (None | RunResponseSensitiveInputAliasesType0 | Unset):
        usage_metadata (None | RunResponseUsageMetadataType0 | Unset): Arbitrary usage/billing metadata captured during
            a run (schema is flexible)
        session_id (None | Unset | UUID):
        session_alias (None | str | Unset):
        release_session_after (bool | None | Unset):
        started_at (datetime.datetime | None | Unset):
        ended_at (datetime.datetime | None | Unset):
    """

    workflow_id: UUID
    machine_id: None | UUID
    id: UUID
    status: RunStatus
    created_at: datetime.datetime
    user_id: None | Unset | UUID = UNSET
    organization_id: None | str | Unset = UNSET
    error: list[str] | None | Unset = UNSET
    output_data: None | RunResponseOutputDataType0 | Unset = UNSET
    input_attachment_ids: list[str] | None | Unset = UNSET
    output_attachment_ids: list[str] | None | Unset = UNSET
    run_message_history: list[RunResponseRunMessageHistoryType0Item] | None | Unset = UNSET
    input_values: None | RunResponseInputValuesType0 | Unset = UNSET
    pool_ids: list[UUID] | None | Unset = UNSET
    sensitive_input_aliases: None | RunResponseSensitiveInputAliasesType0 | Unset = UNSET
    usage_metadata: None | RunResponseUsageMetadataType0 | Unset = UNSET
    session_id: None | Unset | UUID = UNSET
    session_alias: None | str | Unset = UNSET
    release_session_after: bool | None | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_response_input_values_type_0 import RunResponseInputValuesType0
        from ..models.run_response_output_data_type_0 import RunResponseOutputDataType0
        from ..models.run_response_sensitive_input_aliases_type_0 import RunResponseSensitiveInputAliasesType0
        from ..models.run_response_usage_metadata_type_0 import RunResponseUsageMetadataType0

        workflow_id = str(self.workflow_id)

        machine_id: None | str
        if isinstance(self.machine_id, UUID):
            machine_id = str(self.machine_id)
        else:
            machine_id = self.machine_id

        id = str(self.id)

        status = self.status.value

        created_at = self.created_at.isoformat()

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        elif isinstance(self.user_id, UUID):
            user_id = str(self.user_id)
        else:
            user_id = self.user_id

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

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
        elif isinstance(self.output_data, RunResponseOutputDataType0):
            output_data = self.output_data.to_dict()
        else:
            output_data = self.output_data

        input_attachment_ids: list[str] | None | Unset
        if isinstance(self.input_attachment_ids, Unset):
            input_attachment_ids = UNSET
        elif isinstance(self.input_attachment_ids, list):
            input_attachment_ids = self.input_attachment_ids

        else:
            input_attachment_ids = self.input_attachment_ids

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
        elif isinstance(self.input_values, RunResponseInputValuesType0):
            input_values = self.input_values.to_dict()
        else:
            input_values = self.input_values

        pool_ids: list[str] | None | Unset
        if isinstance(self.pool_ids, Unset):
            pool_ids = UNSET
        elif isinstance(self.pool_ids, list):
            pool_ids = []
            for pool_ids_type_0_item_data in self.pool_ids:
                pool_ids_type_0_item = str(pool_ids_type_0_item_data)
                pool_ids.append(pool_ids_type_0_item)

        else:
            pool_ids = self.pool_ids

        sensitive_input_aliases: dict[str, Any] | None | Unset
        if isinstance(self.sensitive_input_aliases, Unset):
            sensitive_input_aliases = UNSET
        elif isinstance(self.sensitive_input_aliases, RunResponseSensitiveInputAliasesType0):
            sensitive_input_aliases = self.sensitive_input_aliases.to_dict()
        else:
            sensitive_input_aliases = self.sensitive_input_aliases

        usage_metadata: dict[str, Any] | None | Unset
        if isinstance(self.usage_metadata, Unset):
            usage_metadata = UNSET
        elif isinstance(self.usage_metadata, RunResponseUsageMetadataType0):
            usage_metadata = self.usage_metadata.to_dict()
        else:
            usage_metadata = self.usage_metadata

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        elif isinstance(self.session_id, UUID):
            session_id = str(self.session_id)
        else:
            session_id = self.session_id

        session_alias: None | str | Unset
        if isinstance(self.session_alias, Unset):
            session_alias = UNSET
        else:
            session_alias = self.session_alias

        release_session_after: bool | None | Unset
        if isinstance(self.release_session_after, Unset):
            release_session_after = UNSET
        else:
            release_session_after = self.release_session_after

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_id": workflow_id,
                "machine_id": machine_id,
                "id": id,
                "status": status,
                "created_at": created_at,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if error is not UNSET:
            field_dict["error"] = error
        if output_data is not UNSET:
            field_dict["output_data"] = output_data
        if input_attachment_ids is not UNSET:
            field_dict["input_attachment_ids"] = input_attachment_ids
        if output_attachment_ids is not UNSET:
            field_dict["output_attachment_ids"] = output_attachment_ids
        if run_message_history is not UNSET:
            field_dict["run_message_history"] = run_message_history
        if input_values is not UNSET:
            field_dict["input_values"] = input_values
        if pool_ids is not UNSET:
            field_dict["pool_ids"] = pool_ids
        if sensitive_input_aliases is not UNSET:
            field_dict["sensitive_input_aliases"] = sensitive_input_aliases
        if usage_metadata is not UNSET:
            field_dict["usage_metadata"] = usage_metadata
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if session_alias is not UNSET:
            field_dict["session_alias"] = session_alias
        if release_session_after is not UNSET:
            field_dict["release_session_after"] = release_session_after
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_response_input_values_type_0 import RunResponseInputValuesType0
        from ..models.run_response_output_data_type_0 import RunResponseOutputDataType0
        from ..models.run_response_run_message_history_type_0_item import RunResponseRunMessageHistoryType0Item
        from ..models.run_response_sensitive_input_aliases_type_0 import RunResponseSensitiveInputAliasesType0
        from ..models.run_response_usage_metadata_type_0 import RunResponseUsageMetadataType0

        d = dict(src_dict)
        workflow_id = UUID(d.pop("workflow_id"))

        def _parse_machine_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                machine_id_type_0 = UUID(data)

                return machine_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        machine_id = _parse_machine_id(d.pop("machine_id"))

        id = UUID(d.pop("id"))

        status = RunStatus(d.pop("status"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_user_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_id_type_0 = UUID(data)

                return user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

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

        def _parse_output_data(data: object) -> None | RunResponseOutputDataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_data_type_0 = RunResponseOutputDataType0.from_dict(data)

                return output_data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunResponseOutputDataType0 | Unset, data)

        output_data = _parse_output_data(d.pop("output_data", UNSET))

        def _parse_input_attachment_ids(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_attachment_ids_type_0 = cast(list[str], data)

                return input_attachment_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        input_attachment_ids = _parse_input_attachment_ids(d.pop("input_attachment_ids", UNSET))

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

        def _parse_run_message_history(data: object) -> list[RunResponseRunMessageHistoryType0Item] | None | Unset:
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
                    run_message_history_type_0_item = RunResponseRunMessageHistoryType0Item.from_dict(
                        run_message_history_type_0_item_data
                    )

                    run_message_history_type_0.append(run_message_history_type_0_item)

                return run_message_history_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[RunResponseRunMessageHistoryType0Item] | None | Unset, data)

        run_message_history = _parse_run_message_history(d.pop("run_message_history", UNSET))

        def _parse_input_values(data: object) -> None | RunResponseInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_values_type_0 = RunResponseInputValuesType0.from_dict(data)

                return input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunResponseInputValuesType0 | Unset, data)

        input_values = _parse_input_values(d.pop("input_values", UNSET))

        def _parse_pool_ids(data: object) -> list[UUID] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                pool_ids_type_0 = []
                _pool_ids_type_0 = data
                for pool_ids_type_0_item_data in _pool_ids_type_0:
                    pool_ids_type_0_item = UUID(pool_ids_type_0_item_data)

                    pool_ids_type_0.append(pool_ids_type_0_item)

                return pool_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[UUID] | None | Unset, data)

        pool_ids = _parse_pool_ids(d.pop("pool_ids", UNSET))

        def _parse_sensitive_input_aliases(data: object) -> None | RunResponseSensitiveInputAliasesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sensitive_input_aliases_type_0 = RunResponseSensitiveInputAliasesType0.from_dict(data)

                return sensitive_input_aliases_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunResponseSensitiveInputAliasesType0 | Unset, data)

        sensitive_input_aliases = _parse_sensitive_input_aliases(d.pop("sensitive_input_aliases", UNSET))

        def _parse_usage_metadata(data: object) -> None | RunResponseUsageMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                usage_metadata_type_0 = RunResponseUsageMetadataType0.from_dict(data)

                return usage_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunResponseUsageMetadataType0 | Unset, data)

        usage_metadata = _parse_usage_metadata(d.pop("usage_metadata", UNSET))

        def _parse_session_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                session_id_type_0 = UUID(data)

                return session_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        def _parse_session_alias(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_alias = _parse_session_alias(d.pop("session_alias", UNSET))

        def _parse_release_session_after(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        release_session_after = _parse_release_session_after(d.pop("release_session_after", UNSET))

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

        run_response = cls(
            workflow_id=workflow_id,
            machine_id=machine_id,
            id=id,
            status=status,
            created_at=created_at,
            user_id=user_id,
            organization_id=organization_id,
            error=error,
            output_data=output_data,
            input_attachment_ids=input_attachment_ids,
            output_attachment_ids=output_attachment_ids,
            run_message_history=run_message_history,
            input_values=input_values,
            pool_ids=pool_ids,
            sensitive_input_aliases=sensitive_input_aliases,
            usage_metadata=usage_metadata,
            session_id=session_id,
            session_alias=session_alias,
            release_session_after=release_session_after,
            started_at=started_at,
            ended_at=ended_at,
        )

        run_response.additional_properties = d
        return run_response

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
