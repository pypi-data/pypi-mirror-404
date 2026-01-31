from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_input import FileInput
    from ..models.run_retry_input_values_type_0 import RunRetryInputValuesType0
    from ..models.run_retry_sensitive_input_values_type_0 import RunRetrySensitiveInputValuesType0


T = TypeVar("T", bound="RunRetry")


@_attrs_define
class RunRetry:
    """Options for retrying an existing run in-place (same run_id).

    Notes:
    - If `file_inputs` are provided, existing input attachments are replaced.
    - Prior outputs, history, and output attachments are always cleared as part of retry.
    - Retry is only allowed for terminal runs (success, error, or cancelled).

        Attributes:
            input_values (None | RunRetryInputValuesType0 | Unset): Override input values for workflow variables
            sensitive_input_values (None | RunRetrySensitiveInputValuesType0 | Unset): Provide new sensitive inputs
                (supports nested objects); stored in vault and mapped to aliases
            file_inputs (list[FileInput] | None | Unset): Provide new input files for this retry; replaces existing input
                attachments
            machine_id (None | Unset | UUID): Override specific machine for this retry
            pool_ids (list[UUID] | None | Unset): Override pool filters if not using a specific machine
            reuse_session (bool | None | Unset): Keep existing session_id. If false and no session_id provided, clears
                session fields Default: True.
            session_id (None | Unset | UUID): Set/override session_id for this retry
            release_session_after (bool | None | Unset): Override release_session_after behavior for this retry
    """

    input_values: None | RunRetryInputValuesType0 | Unset = UNSET
    sensitive_input_values: None | RunRetrySensitiveInputValuesType0 | Unset = UNSET
    file_inputs: list[FileInput] | None | Unset = UNSET
    machine_id: None | Unset | UUID = UNSET
    pool_ids: list[UUID] | None | Unset = UNSET
    reuse_session: bool | None | Unset = True
    session_id: None | Unset | UUID = UNSET
    release_session_after: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_retry_input_values_type_0 import RunRetryInputValuesType0
        from ..models.run_retry_sensitive_input_values_type_0 import RunRetrySensitiveInputValuesType0

        input_values: dict[str, Any] | None | Unset
        if isinstance(self.input_values, Unset):
            input_values = UNSET
        elif isinstance(self.input_values, RunRetryInputValuesType0):
            input_values = self.input_values.to_dict()
        else:
            input_values = self.input_values

        sensitive_input_values: dict[str, Any] | None | Unset
        if isinstance(self.sensitive_input_values, Unset):
            sensitive_input_values = UNSET
        elif isinstance(self.sensitive_input_values, RunRetrySensitiveInputValuesType0):
            sensitive_input_values = self.sensitive_input_values.to_dict()
        else:
            sensitive_input_values = self.sensitive_input_values

        file_inputs: list[dict[str, Any]] | None | Unset
        if isinstance(self.file_inputs, Unset):
            file_inputs = UNSET
        elif isinstance(self.file_inputs, list):
            file_inputs = []
            for file_inputs_type_0_item_data in self.file_inputs:
                file_inputs_type_0_item = file_inputs_type_0_item_data.to_dict()
                file_inputs.append(file_inputs_type_0_item)

        else:
            file_inputs = self.file_inputs

        machine_id: None | str | Unset
        if isinstance(self.machine_id, Unset):
            machine_id = UNSET
        elif isinstance(self.machine_id, UUID):
            machine_id = str(self.machine_id)
        else:
            machine_id = self.machine_id

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

        reuse_session: bool | None | Unset
        if isinstance(self.reuse_session, Unset):
            reuse_session = UNSET
        else:
            reuse_session = self.reuse_session

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        elif isinstance(self.session_id, UUID):
            session_id = str(self.session_id)
        else:
            session_id = self.session_id

        release_session_after: bool | None | Unset
        if isinstance(self.release_session_after, Unset):
            release_session_after = UNSET
        else:
            release_session_after = self.release_session_after

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if input_values is not UNSET:
            field_dict["input_values"] = input_values
        if sensitive_input_values is not UNSET:
            field_dict["sensitive_input_values"] = sensitive_input_values
        if file_inputs is not UNSET:
            field_dict["file_inputs"] = file_inputs
        if machine_id is not UNSET:
            field_dict["machine_id"] = machine_id
        if pool_ids is not UNSET:
            field_dict["pool_ids"] = pool_ids
        if reuse_session is not UNSET:
            field_dict["reuse_session"] = reuse_session
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if release_session_after is not UNSET:
            field_dict["release_session_after"] = release_session_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_input import FileInput
        from ..models.run_retry_input_values_type_0 import RunRetryInputValuesType0
        from ..models.run_retry_sensitive_input_values_type_0 import RunRetrySensitiveInputValuesType0

        d = dict(src_dict)

        def _parse_input_values(data: object) -> None | RunRetryInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_values_type_0 = RunRetryInputValuesType0.from_dict(data)

                return input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunRetryInputValuesType0 | Unset, data)

        input_values = _parse_input_values(d.pop("input_values", UNSET))

        def _parse_sensitive_input_values(data: object) -> None | RunRetrySensitiveInputValuesType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sensitive_input_values_type_0 = RunRetrySensitiveInputValuesType0.from_dict(data)

                return sensitive_input_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunRetrySensitiveInputValuesType0 | Unset, data)

        sensitive_input_values = _parse_sensitive_input_values(d.pop("sensitive_input_values", UNSET))

        def _parse_file_inputs(data: object) -> list[FileInput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                file_inputs_type_0 = []
                _file_inputs_type_0 = data
                for file_inputs_type_0_item_data in _file_inputs_type_0:
                    file_inputs_type_0_item = FileInput.from_dict(file_inputs_type_0_item_data)

                    file_inputs_type_0.append(file_inputs_type_0_item)

                return file_inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[FileInput] | None | Unset, data)

        file_inputs = _parse_file_inputs(d.pop("file_inputs", UNSET))

        def _parse_machine_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                machine_id_type_0 = UUID(data)

                return machine_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        machine_id = _parse_machine_id(d.pop("machine_id", UNSET))

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

        def _parse_reuse_session(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        reuse_session = _parse_reuse_session(d.pop("reuse_session", UNSET))

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

        def _parse_release_session_after(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        release_session_after = _parse_release_session_after(d.pop("release_session_after", UNSET))

        run_retry = cls(
            input_values=input_values,
            sensitive_input_values=sensitive_input_values,
            file_inputs=file_inputs,
            machine_id=machine_id,
            pool_ids=pool_ids,
            reuse_session=reuse_session,
            session_id=session_id,
            release_session_after=release_session_after,
        )

        run_retry.additional_properties = d
        return run_retry

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
