from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chain_step_inputs_type_0 import ChainStepInputsType0
    from ..models.chain_step_sensitive_inputs_type_0 import ChainStepSensitiveInputsType0


T = TypeVar("T", bound="ChainStep")


@_attrs_define
class ChainStep:
    """One step within a chain

    Attributes:
        workflow_id (UUID):
        session_alias (None | str | Unset): Alias to persist this step's outputs within the session
        inputs (ChainStepInputsType0 | None | Unset): Step-specific inputs; values can be strings, objects, arrays, or
            {$ref: 'alias.outputs.path'} references
        sensitive_inputs (ChainStepSensitiveInputsType0 | None | Unset): Step-specific sensitive inputs (supports nested
            objects) that override or extend shared_sensitive_inputs
    """

    workflow_id: UUID
    session_alias: None | str | Unset = UNSET
    inputs: ChainStepInputsType0 | None | Unset = UNSET
    sensitive_inputs: ChainStepSensitiveInputsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chain_step_inputs_type_0 import ChainStepInputsType0
        from ..models.chain_step_sensitive_inputs_type_0 import ChainStepSensitiveInputsType0

        workflow_id = str(self.workflow_id)

        session_alias: None | str | Unset
        if isinstance(self.session_alias, Unset):
            session_alias = UNSET
        else:
            session_alias = self.session_alias

        inputs: dict[str, Any] | None | Unset
        if isinstance(self.inputs, Unset):
            inputs = UNSET
        elif isinstance(self.inputs, ChainStepInputsType0):
            inputs = self.inputs.to_dict()
        else:
            inputs = self.inputs

        sensitive_inputs: dict[str, Any] | None | Unset
        if isinstance(self.sensitive_inputs, Unset):
            sensitive_inputs = UNSET
        elif isinstance(self.sensitive_inputs, ChainStepSensitiveInputsType0):
            sensitive_inputs = self.sensitive_inputs.to_dict()
        else:
            sensitive_inputs = self.sensitive_inputs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_id": workflow_id,
            }
        )
        if session_alias is not UNSET:
            field_dict["session_alias"] = session_alias
        if inputs is not UNSET:
            field_dict["inputs"] = inputs
        if sensitive_inputs is not UNSET:
            field_dict["sensitive_inputs"] = sensitive_inputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chain_step_inputs_type_0 import ChainStepInputsType0
        from ..models.chain_step_sensitive_inputs_type_0 import ChainStepSensitiveInputsType0

        d = dict(src_dict)
        workflow_id = UUID(d.pop("workflow_id"))

        def _parse_session_alias(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_alias = _parse_session_alias(d.pop("session_alias", UNSET))

        def _parse_inputs(data: object) -> ChainStepInputsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                inputs_type_0 = ChainStepInputsType0.from_dict(data)

                return inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChainStepInputsType0 | None | Unset, data)

        inputs = _parse_inputs(d.pop("inputs", UNSET))

        def _parse_sensitive_inputs(data: object) -> ChainStepSensitiveInputsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sensitive_inputs_type_0 = ChainStepSensitiveInputsType0.from_dict(data)

                return sensitive_inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChainStepSensitiveInputsType0 | None | Unset, data)

        sensitive_inputs = _parse_sensitive_inputs(d.pop("sensitive_inputs", UNSET))

        chain_step = cls(
            workflow_id=workflow_id,
            session_alias=session_alias,
            inputs=inputs,
            sensitive_inputs=sensitive_inputs,
        )

        chain_step.additional_properties = d
        return chain_step

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
