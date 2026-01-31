from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.model_configuration_create import ModelConfigurationCreate
from ...models.model_configuration_response import ModelConfigurationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ModelConfigurationCreate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/model-configurations",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ModelConfigurationResponse | None:
    if response.status_code == 201:
        response_201 = ModelConfigurationResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | ModelConfigurationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelConfigurationResponse]:
    """Create Model Configuration

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationCreate): Create a model configuration.

            `api_key` is the raw secret material; it will be stored in Basis Theory and only the alias
            is persisted.
            For providers that Cyberdesk does not provide keys for, `api_key` is required.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelConfigurationResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | ModelConfigurationResponse | None:
    """Create Model Configuration

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationCreate): Create a model configuration.

            `api_key` is the raw secret material; it will be stored in Basis Theory and only the alias
            is persisted.
            For providers that Cyberdesk does not provide keys for, `api_key` is required.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelConfigurationResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelConfigurationResponse]:
    """Create Model Configuration

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationCreate): Create a model configuration.

            `api_key` is the raw secret material; it will be stored in Basis Theory and only the alias
            is persisted.
            For providers that Cyberdesk does not provide keys for, `api_key` is required.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelConfigurationResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | ModelConfigurationResponse | None:
    """Create Model Configuration

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationCreate): Create a model configuration.

            `api_key` is the raw secret material; it will be stored in Basis Theory and only the alias
            is persisted.
            For providers that Cyberdesk does not provide keys for, `api_key` is required.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelConfigurationResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
