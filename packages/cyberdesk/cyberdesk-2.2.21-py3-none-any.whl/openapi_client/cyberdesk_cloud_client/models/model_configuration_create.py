from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.model_configuration_create_additional_params_type_0 import (
        ModelConfigurationCreateAdditionalParamsType0,
    )


T = TypeVar("T", bound="ModelConfigurationCreate")


@_attrs_define
class ModelConfigurationCreate:
    """Create a model configuration.

    `api_key` is the raw secret material; it will be stored in Basis Theory and only the alias is persisted.
    For providers that Cyberdesk does not provide keys for, `api_key` is required.

        Attributes:
            name (str):
            provider (str): LangChain provider name (e.g. 'anthropic', 'openai').
            model (str): Provider model identifier (e.g. 'claude-sonnet-4-5-20250929').
            description (None | str | Unset):
            temperature (float | None | Unset):
            max_tokens (int | None | Unset):
            timeout_seconds (float | None | Unset):
            max_retries (int | None | Unset):
            additional_params (ModelConfigurationCreateAdditionalParamsType0 | None | Unset): Provider-specific kwargs
                passed through to LangChain.
            is_computer_use_model (bool | Unset): True if this model has native computer use capabilities. If True, can be
                used for main agent, focused actions, and fallbacks for those agents. Default: False.
            api_key (None | str | Unset): Raw API key (stored in Basis Theory; never persisted directly).
    """

    name: str
    provider: str
    model: str
    description: None | str | Unset = UNSET
    temperature: float | None | Unset = UNSET
    max_tokens: int | None | Unset = UNSET
    timeout_seconds: float | None | Unset = UNSET
    max_retries: int | None | Unset = UNSET
    additional_params: ModelConfigurationCreateAdditionalParamsType0 | None | Unset = UNSET
    is_computer_use_model: bool | Unset = False
    api_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.model_configuration_create_additional_params_type_0 import (
            ModelConfigurationCreateAdditionalParamsType0,
        )

        name = self.name

        provider = self.provider

        model = self.model

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        temperature: float | None | Unset
        if isinstance(self.temperature, Unset):
            temperature = UNSET
        else:
            temperature = self.temperature

        max_tokens: int | None | Unset
        if isinstance(self.max_tokens, Unset):
            max_tokens = UNSET
        else:
            max_tokens = self.max_tokens

        timeout_seconds: float | None | Unset
        if isinstance(self.timeout_seconds, Unset):
            timeout_seconds = UNSET
        else:
            timeout_seconds = self.timeout_seconds

        max_retries: int | None | Unset
        if isinstance(self.max_retries, Unset):
            max_retries = UNSET
        else:
            max_retries = self.max_retries

        additional_params: dict[str, Any] | None | Unset
        if isinstance(self.additional_params, Unset):
            additional_params = UNSET
        elif isinstance(self.additional_params, ModelConfigurationCreateAdditionalParamsType0):
            additional_params = self.additional_params.to_dict()
        else:
            additional_params = self.additional_params

        is_computer_use_model = self.is_computer_use_model

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "provider": provider,
                "model": model,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if timeout_seconds is not UNSET:
            field_dict["timeout_seconds"] = timeout_seconds
        if max_retries is not UNSET:
            field_dict["max_retries"] = max_retries
        if additional_params is not UNSET:
            field_dict["additional_params"] = additional_params
        if is_computer_use_model is not UNSET:
            field_dict["is_computer_use_model"] = is_computer_use_model
        if api_key is not UNSET:
            field_dict["api_key"] = api_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.model_configuration_create_additional_params_type_0 import (
            ModelConfigurationCreateAdditionalParamsType0,
        )

        d = dict(src_dict)
        name = d.pop("name")

        provider = d.pop("provider")

        model = d.pop("model")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_temperature(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        temperature = _parse_temperature(d.pop("temperature", UNSET))

        def _parse_max_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_tokens = _parse_max_tokens(d.pop("max_tokens", UNSET))

        def _parse_timeout_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        timeout_seconds = _parse_timeout_seconds(d.pop("timeout_seconds", UNSET))

        def _parse_max_retries(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_retries = _parse_max_retries(d.pop("max_retries", UNSET))

        def _parse_additional_params(data: object) -> ModelConfigurationCreateAdditionalParamsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                additional_params_type_0 = ModelConfigurationCreateAdditionalParamsType0.from_dict(data)

                return additional_params_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModelConfigurationCreateAdditionalParamsType0 | None | Unset, data)

        additional_params = _parse_additional_params(d.pop("additional_params", UNSET))

        is_computer_use_model = d.pop("is_computer_use_model", UNSET)

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        model_configuration_create = cls(
            name=name,
            provider=provider,
            model=model,
            description=description,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            additional_params=additional_params,
            is_computer_use_model=is_computer_use_model,
            api_key=api_key,
        )

        model_configuration_create.additional_properties = d
        return model_configuration_create

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
