from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chain_step import ChainStep
    from ..models.file_input import FileInput
    from ..models.workflow_chain_create_shared_inputs_type_0 import WorkflowChainCreateSharedInputsType0
    from ..models.workflow_chain_create_shared_sensitive_inputs_type_0 import (
        WorkflowChainCreateSharedSensitiveInputsType0,
    )


T = TypeVar("T", bound="WorkflowChainCreate")


@_attrs_define
class WorkflowChainCreate:
    """Request to create and run a multi-step chain on a single reserved session/machine

    Attributes:
        steps (list[ChainStep]):
        shared_inputs (None | Unset | WorkflowChainCreateSharedInputsType0):
        shared_sensitive_inputs (None | Unset | WorkflowChainCreateSharedSensitiveInputsType0): Shared sensitive inputs
            (supports nested objects) for all steps
        shared_file_inputs (list[FileInput] | None | Unset):
        keep_session_after_completion (bool | None | Unset):  Default: False.
        machine_id (None | Unset | UUID):
        pool_ids (list[UUID] | None | Unset): Pool IDs to filter available machines when starting a new session. Machine
            must belong to ALL of these pools (intersection). Ignored when machine_id is provided.
        session_id (None | Unset | UUID):
    """

    steps: list[ChainStep]
    shared_inputs: None | Unset | WorkflowChainCreateSharedInputsType0 = UNSET
    shared_sensitive_inputs: None | Unset | WorkflowChainCreateSharedSensitiveInputsType0 = UNSET
    shared_file_inputs: list[FileInput] | None | Unset = UNSET
    keep_session_after_completion: bool | None | Unset = False
    machine_id: None | Unset | UUID = UNSET
    pool_ids: list[UUID] | None | Unset = UNSET
    session_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.workflow_chain_create_shared_inputs_type_0 import WorkflowChainCreateSharedInputsType0
        from ..models.workflow_chain_create_shared_sensitive_inputs_type_0 import (
            WorkflowChainCreateSharedSensitiveInputsType0,
        )

        steps = []
        for steps_item_data in self.steps:
            steps_item = steps_item_data.to_dict()
            steps.append(steps_item)

        shared_inputs: dict[str, Any] | None | Unset
        if isinstance(self.shared_inputs, Unset):
            shared_inputs = UNSET
        elif isinstance(self.shared_inputs, WorkflowChainCreateSharedInputsType0):
            shared_inputs = self.shared_inputs.to_dict()
        else:
            shared_inputs = self.shared_inputs

        shared_sensitive_inputs: dict[str, Any] | None | Unset
        if isinstance(self.shared_sensitive_inputs, Unset):
            shared_sensitive_inputs = UNSET
        elif isinstance(self.shared_sensitive_inputs, WorkflowChainCreateSharedSensitiveInputsType0):
            shared_sensitive_inputs = self.shared_sensitive_inputs.to_dict()
        else:
            shared_sensitive_inputs = self.shared_sensitive_inputs

        shared_file_inputs: list[dict[str, Any]] | None | Unset
        if isinstance(self.shared_file_inputs, Unset):
            shared_file_inputs = UNSET
        elif isinstance(self.shared_file_inputs, list):
            shared_file_inputs = []
            for shared_file_inputs_type_0_item_data in self.shared_file_inputs:
                shared_file_inputs_type_0_item = shared_file_inputs_type_0_item_data.to_dict()
                shared_file_inputs.append(shared_file_inputs_type_0_item)

        else:
            shared_file_inputs = self.shared_file_inputs

        keep_session_after_completion: bool | None | Unset
        if isinstance(self.keep_session_after_completion, Unset):
            keep_session_after_completion = UNSET
        else:
            keep_session_after_completion = self.keep_session_after_completion

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

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        elif isinstance(self.session_id, UUID):
            session_id = str(self.session_id)
        else:
            session_id = self.session_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "steps": steps,
            }
        )
        if shared_inputs is not UNSET:
            field_dict["shared_inputs"] = shared_inputs
        if shared_sensitive_inputs is not UNSET:
            field_dict["shared_sensitive_inputs"] = shared_sensitive_inputs
        if shared_file_inputs is not UNSET:
            field_dict["shared_file_inputs"] = shared_file_inputs
        if keep_session_after_completion is not UNSET:
            field_dict["keep_session_after_completion"] = keep_session_after_completion
        if machine_id is not UNSET:
            field_dict["machine_id"] = machine_id
        if pool_ids is not UNSET:
            field_dict["pool_ids"] = pool_ids
        if session_id is not UNSET:
            field_dict["session_id"] = session_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chain_step import ChainStep
        from ..models.file_input import FileInput
        from ..models.workflow_chain_create_shared_inputs_type_0 import WorkflowChainCreateSharedInputsType0
        from ..models.workflow_chain_create_shared_sensitive_inputs_type_0 import (
            WorkflowChainCreateSharedSensitiveInputsType0,
        )

        d = dict(src_dict)
        steps = []
        _steps = d.pop("steps")
        for steps_item_data in _steps:
            steps_item = ChainStep.from_dict(steps_item_data)

            steps.append(steps_item)

        def _parse_shared_inputs(data: object) -> None | Unset | WorkflowChainCreateSharedInputsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                shared_inputs_type_0 = WorkflowChainCreateSharedInputsType0.from_dict(data)

                return shared_inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WorkflowChainCreateSharedInputsType0, data)

        shared_inputs = _parse_shared_inputs(d.pop("shared_inputs", UNSET))

        def _parse_shared_sensitive_inputs(
            data: object,
        ) -> None | Unset | WorkflowChainCreateSharedSensitiveInputsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                shared_sensitive_inputs_type_0 = WorkflowChainCreateSharedSensitiveInputsType0.from_dict(data)

                return shared_sensitive_inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WorkflowChainCreateSharedSensitiveInputsType0, data)

        shared_sensitive_inputs = _parse_shared_sensitive_inputs(d.pop("shared_sensitive_inputs", UNSET))

        def _parse_shared_file_inputs(data: object) -> list[FileInput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                shared_file_inputs_type_0 = []
                _shared_file_inputs_type_0 = data
                for shared_file_inputs_type_0_item_data in _shared_file_inputs_type_0:
                    shared_file_inputs_type_0_item = FileInput.from_dict(shared_file_inputs_type_0_item_data)

                    shared_file_inputs_type_0.append(shared_file_inputs_type_0_item)

                return shared_file_inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[FileInput] | None | Unset, data)

        shared_file_inputs = _parse_shared_file_inputs(d.pop("shared_file_inputs", UNSET))

        def _parse_keep_session_after_completion(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        keep_session_after_completion = _parse_keep_session_after_completion(
            d.pop("keep_session_after_completion", UNSET)
        )

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

        workflow_chain_create = cls(
            steps=steps,
            shared_inputs=shared_inputs,
            shared_sensitive_inputs=shared_sensitive_inputs,
            shared_file_inputs=shared_file_inputs,
            keep_session_after_completion=keep_session_after_completion,
            machine_id=machine_id,
            pool_ids=pool_ids,
            session_id=session_id,
        )

        workflow_chain_create.additional_properties = d
        return workflow_chain_create

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
