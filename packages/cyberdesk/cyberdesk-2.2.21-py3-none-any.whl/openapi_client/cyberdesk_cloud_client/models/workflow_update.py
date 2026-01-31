from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workflow_model_metadata import WorkflowModelMetadata


T = TypeVar("T", bound="WorkflowUpdate")


@_attrs_define
class WorkflowUpdate:
    """Schema for updating a workflow

    Attributes:
        name (None | str | Unset):
        main_prompt (None | str | Unset):
        output_schema (None | str | Unset): JSON schema for output data transformation
        includes_file_exports (bool | None | Unset): Enable AI-based file export detection
        is_webhooks_enabled (bool | None | Unset): Send webhook on run completion
        model_metadata (None | Unset | WorkflowModelMetadata): Optional workflow-level model configuration metadata
            (main agent + fallbacks).
    """

    name: None | str | Unset = UNSET
    main_prompt: None | str | Unset = UNSET
    output_schema: None | str | Unset = UNSET
    includes_file_exports: bool | None | Unset = UNSET
    is_webhooks_enabled: bool | None | Unset = UNSET
    model_metadata: None | Unset | WorkflowModelMetadata = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.workflow_model_metadata import WorkflowModelMetadata

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        main_prompt: None | str | Unset
        if isinstance(self.main_prompt, Unset):
            main_prompt = UNSET
        else:
            main_prompt = self.main_prompt

        output_schema: None | str | Unset
        if isinstance(self.output_schema, Unset):
            output_schema = UNSET
        else:
            output_schema = self.output_schema

        includes_file_exports: bool | None | Unset
        if isinstance(self.includes_file_exports, Unset):
            includes_file_exports = UNSET
        else:
            includes_file_exports = self.includes_file_exports

        is_webhooks_enabled: bool | None | Unset
        if isinstance(self.is_webhooks_enabled, Unset):
            is_webhooks_enabled = UNSET
        else:
            is_webhooks_enabled = self.is_webhooks_enabled

        model_metadata: dict[str, Any] | None | Unset
        if isinstance(self.model_metadata, Unset):
            model_metadata = UNSET
        elif isinstance(self.model_metadata, WorkflowModelMetadata):
            model_metadata = self.model_metadata.to_dict()
        else:
            model_metadata = self.model_metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if main_prompt is not UNSET:
            field_dict["main_prompt"] = main_prompt
        if output_schema is not UNSET:
            field_dict["output_schema"] = output_schema
        if includes_file_exports is not UNSET:
            field_dict["includes_file_exports"] = includes_file_exports
        if is_webhooks_enabled is not UNSET:
            field_dict["is_webhooks_enabled"] = is_webhooks_enabled
        if model_metadata is not UNSET:
            field_dict["model_metadata"] = model_metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workflow_model_metadata import WorkflowModelMetadata

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_main_prompt(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        main_prompt = _parse_main_prompt(d.pop("main_prompt", UNSET))

        def _parse_output_schema(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_schema = _parse_output_schema(d.pop("output_schema", UNSET))

        def _parse_includes_file_exports(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        includes_file_exports = _parse_includes_file_exports(d.pop("includes_file_exports", UNSET))

        def _parse_is_webhooks_enabled(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_webhooks_enabled = _parse_is_webhooks_enabled(d.pop("is_webhooks_enabled", UNSET))

        def _parse_model_metadata(data: object) -> None | Unset | WorkflowModelMetadata:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                model_metadata_type_0 = WorkflowModelMetadata.from_dict(data)

                return model_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WorkflowModelMetadata, data)

        model_metadata = _parse_model_metadata(d.pop("model_metadata", UNSET))

        workflow_update = cls(
            name=name,
            main_prompt=main_prompt,
            output_schema=output_schema,
            includes_file_exports=includes_file_exports,
            is_webhooks_enabled=is_webhooks_enabled,
            model_metadata=model_metadata,
        )

        workflow_update.additional_properties = d
        return workflow_update

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
