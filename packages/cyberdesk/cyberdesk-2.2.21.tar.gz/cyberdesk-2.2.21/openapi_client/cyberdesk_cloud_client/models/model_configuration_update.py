from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.model_configuration_update_additional_params_type_0 import (
        ModelConfigurationUpdateAdditionalParamsType0,
    )


T = TypeVar("T", bound="ModelConfigurationUpdate")


@_attrs_define
class ModelConfigurationUpdate:
    """Update a model configuration (organization-owned only).

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        provider (None | str | Unset):
        model (None | str | Unset):
        api_key (None | str | Unset): Raw API key; if provided, replaces the stored alias.
        clear_api_key (bool | None | Unset): If true, clears any stored api_key_alias (reverts to Cyberdesk-provided key
            if supported).
        temperature (float | None | Unset):
        max_tokens (int | None | Unset):
        timeout_seconds (float | None | Unset):
        max_retries (int | None | Unset):
        additional_params (ModelConfigurationUpdateAdditionalParamsType0 | None | Unset):
        is_computer_use_model (bool | None | Unset):
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    provider: None | str | Unset = UNSET
    model: None | str | Unset = UNSET
    api_key: None | str | Unset = UNSET
    clear_api_key: bool | None | Unset = UNSET
    temperature: float | None | Unset = UNSET
    max_tokens: int | None | Unset = UNSET
    timeout_seconds: float | None | Unset = UNSET
    max_retries: int | None | Unset = UNSET
    additional_params: ModelConfigurationUpdateAdditionalParamsType0 | None | Unset = UNSET
    is_computer_use_model: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.model_configuration_update_additional_params_type_0 import (
            ModelConfigurationUpdateAdditionalParamsType0,
        )

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        else:
            provider = self.provider

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        clear_api_key: bool | None | Unset
        if isinstance(self.clear_api_key, Unset):
            clear_api_key = UNSET
        else:
            clear_api_key = self.clear_api_key

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
        elif isinstance(self.additional_params, ModelConfigurationUpdateAdditionalParamsType0):
            additional_params = self.additional_params.to_dict()
        else:
            additional_params = self.additional_params

        is_computer_use_model: bool | None | Unset
        if isinstance(self.is_computer_use_model, Unset):
            is_computer_use_model = UNSET
        else:
            is_computer_use_model = self.is_computer_use_model

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if provider is not UNSET:
            field_dict["provider"] = provider
        if model is not UNSET:
            field_dict["model"] = model
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if clear_api_key is not UNSET:
            field_dict["clear_api_key"] = clear_api_key
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.model_configuration_update_additional_params_type_0 import (
            ModelConfigurationUpdateAdditionalParamsType0,
        )

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_provider(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_clear_api_key(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        clear_api_key = _parse_clear_api_key(d.pop("clear_api_key", UNSET))

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

        def _parse_additional_params(data: object) -> ModelConfigurationUpdateAdditionalParamsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                additional_params_type_0 = ModelConfigurationUpdateAdditionalParamsType0.from_dict(data)

                return additional_params_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModelConfigurationUpdateAdditionalParamsType0 | None | Unset, data)

        additional_params = _parse_additional_params(d.pop("additional_params", UNSET))

        def _parse_is_computer_use_model(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_computer_use_model = _parse_is_computer_use_model(d.pop("is_computer_use_model", UNSET))

        model_configuration_update = cls(
            name=name,
            description=description,
            provider=provider,
            model=model,
            api_key=api_key,
            clear_api_key=clear_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            additional_params=additional_params,
            is_computer_use_model=is_computer_use_model,
        )

        model_configuration_update.additional_properties = d
        return model_configuration_update

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
