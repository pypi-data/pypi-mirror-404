from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkflowModelMetadata")


@_attrs_define
class WorkflowModelMetadata:
    """JSONB-backed workflow model configuration metadata.

    Stored on the Workflow row as `model_metadata` to avoid adding many FK columns.
    All fields are optional; when missing/null, the system falls back to Cyberdesk defaults.

        Attributes:
            main_agent_model_id (None | Unset | UUID): ModelConfiguration.id used for the main agent. Null → Cyberdesk
                default.
            fallback_model_1_id (None | Unset | UUID): ModelConfiguration.id used as fallback 1 (global across agents).
            fallback_model_2_id (None | Unset | UUID): ModelConfiguration.id used as fallback 2 (global across agents).
    """

    main_agent_model_id: None | Unset | UUID = UNSET
    fallback_model_1_id: None | Unset | UUID = UNSET
    fallback_model_2_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        main_agent_model_id: None | str | Unset
        if isinstance(self.main_agent_model_id, Unset):
            main_agent_model_id = UNSET
        elif isinstance(self.main_agent_model_id, UUID):
            main_agent_model_id = str(self.main_agent_model_id)
        else:
            main_agent_model_id = self.main_agent_model_id

        fallback_model_1_id: None | str | Unset
        if isinstance(self.fallback_model_1_id, Unset):
            fallback_model_1_id = UNSET
        elif isinstance(self.fallback_model_1_id, UUID):
            fallback_model_1_id = str(self.fallback_model_1_id)
        else:
            fallback_model_1_id = self.fallback_model_1_id

        fallback_model_2_id: None | str | Unset
        if isinstance(self.fallback_model_2_id, Unset):
            fallback_model_2_id = UNSET
        elif isinstance(self.fallback_model_2_id, UUID):
            fallback_model_2_id = str(self.fallback_model_2_id)
        else:
            fallback_model_2_id = self.fallback_model_2_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if main_agent_model_id is not UNSET:
            field_dict["main_agent_model_id"] = main_agent_model_id
        if fallback_model_1_id is not UNSET:
            field_dict["fallback_model_1_id"] = fallback_model_1_id
        if fallback_model_2_id is not UNSET:
            field_dict["fallback_model_2_id"] = fallback_model_2_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_main_agent_model_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                main_agent_model_id_type_0 = UUID(data)

                return main_agent_model_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        main_agent_model_id = _parse_main_agent_model_id(d.pop("main_agent_model_id", UNSET))

        def _parse_fallback_model_1_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                fallback_model_1_id_type_0 = UUID(data)

                return fallback_model_1_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        fallback_model_1_id = _parse_fallback_model_1_id(d.pop("fallback_model_1_id", UNSET))

        def _parse_fallback_model_2_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                fallback_model_2_id_type_0 = UUID(data)

                return fallback_model_2_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        fallback_model_2_id = _parse_fallback_model_2_id(d.pop("fallback_model_2_id", UNSET))

        workflow_model_metadata = cls(
            main_agent_model_id=main_agent_model_id,
            fallback_model_1_id=fallback_model_1_id,
            fallback_model_2_id=fallback_model_2_id,
        )

        workflow_model_metadata.additional_properties = d
        return workflow_model_metadata

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
