from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workflow_model_metadata import WorkflowModelMetadata
    from ..models.workflow_response_old_versions_type_0_item import WorkflowResponseOldVersionsType0Item
    from ..models.workflow_tag_response import WorkflowTagResponse


T = TypeVar("T", bound="WorkflowResponse")


@_attrs_define
class WorkflowResponse:
    """Workflow response schema

    Attributes:
        main_prompt (str):
        id (UUID):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        name (None | str | Unset):
        output_schema (None | str | Unset): JSON schema for output data transformation
        includes_file_exports (bool | Unset): Enable AI-based file export detection Default: False.
        is_webhooks_enabled (bool | Unset): Send webhook on run completion Default: False.
        model_metadata (None | Unset | WorkflowModelMetadata): Optional workflow-level model configuration metadata
            (main agent + fallbacks).
        user_id (None | Unset | UUID):
        organization_id (None | str | Unset):
        includes_input_variables (bool | Unset):  Default: False.
        old_versions (list[WorkflowResponseOldVersionsType0Item] | None | Unset):
        tags (list[WorkflowTagResponse] | None | Unset): Tags assigned to this workflow
    """

    main_prompt: str
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: None | str | Unset = UNSET
    output_schema: None | str | Unset = UNSET
    includes_file_exports: bool | Unset = False
    is_webhooks_enabled: bool | Unset = False
    model_metadata: None | Unset | WorkflowModelMetadata = UNSET
    user_id: None | Unset | UUID = UNSET
    organization_id: None | str | Unset = UNSET
    includes_input_variables: bool | Unset = False
    old_versions: list[WorkflowResponseOldVersionsType0Item] | None | Unset = UNSET
    tags: list[WorkflowTagResponse] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.workflow_model_metadata import WorkflowModelMetadata

        main_prompt = self.main_prompt

        id = str(self.id)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        output_schema: None | str | Unset
        if isinstance(self.output_schema, Unset):
            output_schema = UNSET
        else:
            output_schema = self.output_schema

        includes_file_exports = self.includes_file_exports

        is_webhooks_enabled = self.is_webhooks_enabled

        model_metadata: dict[str, Any] | None | Unset
        if isinstance(self.model_metadata, Unset):
            model_metadata = UNSET
        elif isinstance(self.model_metadata, WorkflowModelMetadata):
            model_metadata = self.model_metadata.to_dict()
        else:
            model_metadata = self.model_metadata

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

        includes_input_variables = self.includes_input_variables

        old_versions: list[dict[str, Any]] | None | Unset
        if isinstance(self.old_versions, Unset):
            old_versions = UNSET
        elif isinstance(self.old_versions, list):
            old_versions = []
            for old_versions_type_0_item_data in self.old_versions:
                old_versions_type_0_item = old_versions_type_0_item_data.to_dict()
                old_versions.append(old_versions_type_0_item)

        else:
            old_versions = self.old_versions

        tags: list[dict[str, Any]] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = []
            for tags_type_0_item_data in self.tags:
                tags_type_0_item = tags_type_0_item_data.to_dict()
                tags.append(tags_type_0_item)

        else:
            tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "main_prompt": main_prompt,
                "id": id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if output_schema is not UNSET:
            field_dict["output_schema"] = output_schema
        if includes_file_exports is not UNSET:
            field_dict["includes_file_exports"] = includes_file_exports
        if is_webhooks_enabled is not UNSET:
            field_dict["is_webhooks_enabled"] = is_webhooks_enabled
        if model_metadata is not UNSET:
            field_dict["model_metadata"] = model_metadata
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if includes_input_variables is not UNSET:
            field_dict["includes_input_variables"] = includes_input_variables
        if old_versions is not UNSET:
            field_dict["old_versions"] = old_versions
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workflow_model_metadata import WorkflowModelMetadata
        from ..models.workflow_response_old_versions_type_0_item import WorkflowResponseOldVersionsType0Item
        from ..models.workflow_tag_response import WorkflowTagResponse

        d = dict(src_dict)
        main_prompt = d.pop("main_prompt")

        id = UUID(d.pop("id"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_output_schema(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_schema = _parse_output_schema(d.pop("output_schema", UNSET))

        includes_file_exports = d.pop("includes_file_exports", UNSET)

        is_webhooks_enabled = d.pop("is_webhooks_enabled", UNSET)

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

        includes_input_variables = d.pop("includes_input_variables", UNSET)

        def _parse_old_versions(data: object) -> list[WorkflowResponseOldVersionsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                old_versions_type_0 = []
                _old_versions_type_0 = data
                for old_versions_type_0_item_data in _old_versions_type_0:
                    old_versions_type_0_item = WorkflowResponseOldVersionsType0Item.from_dict(
                        old_versions_type_0_item_data
                    )

                    old_versions_type_0.append(old_versions_type_0_item)

                return old_versions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[WorkflowResponseOldVersionsType0Item] | None | Unset, data)

        old_versions = _parse_old_versions(d.pop("old_versions", UNSET))

        def _parse_tags(data: object) -> list[WorkflowTagResponse] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = []
                _tags_type_0 = data
                for tags_type_0_item_data in _tags_type_0:
                    tags_type_0_item = WorkflowTagResponse.from_dict(tags_type_0_item_data)

                    tags_type_0.append(tags_type_0_item)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[WorkflowTagResponse] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        workflow_response = cls(
            main_prompt=main_prompt,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            output_schema=output_schema,
            includes_file_exports=includes_file_exports,
            is_webhooks_enabled=is_webhooks_enabled,
            model_metadata=model_metadata,
            user_id=user_id,
            organization_id=organization_id,
            includes_input_variables=includes_input_variables,
            old_versions=old_versions,
            tags=tags,
        )

        workflow_response.additional_properties = d
        return workflow_response

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
