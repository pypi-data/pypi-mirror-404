from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.model_configuration_response import ModelConfigurationResponse
from ...models.model_configuration_update import ModelConfigurationUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    model_configuration_id: UUID,
    *,
    body: ModelConfigurationUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/model-configurations/{model_configuration_id}".format(
            model_configuration_id=quote(str(model_configuration_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ModelConfigurationResponse | None:
    if response.status_code == 200:
        response_200 = ModelConfigurationResponse.from_dict(response.json())

        return response_200

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
    model_configuration_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelConfigurationResponse]:
    """Update Model Configuration

    Args:
        model_configuration_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationUpdate): Update a model configuration (organization-owned only).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelConfigurationResponse]
    """

    kwargs = _get_kwargs(
        model_configuration_id=model_configuration_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    model_configuration_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | ModelConfigurationResponse | None:
    """Update Model Configuration

    Args:
        model_configuration_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationUpdate): Update a model configuration (organization-owned only).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelConfigurationResponse
    """

    return sync_detailed(
        model_configuration_id=model_configuration_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    model_configuration_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelConfigurationResponse]:
    """Update Model Configuration

    Args:
        model_configuration_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationUpdate): Update a model configuration (organization-owned only).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelConfigurationResponse]
    """

    kwargs = _get_kwargs(
        model_configuration_id=model_configuration_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    model_configuration_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ModelConfigurationUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | ModelConfigurationResponse | None:
    """Update Model Configuration

    Args:
        model_configuration_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ModelConfigurationUpdate): Update a model configuration (organization-owned only).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelConfigurationResponse
    """

    return (
        await asyncio_detailed(
            model_configuration_id=model_configuration_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
